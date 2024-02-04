from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from api.models.jwt import JwtTokenData
from api.models.tests import MakeChoice
from dependencies.jwt_token import get_token_data
from api.service.tests import TestsService, ChoiceService
from api.service.test import TestItemService
from dependencies.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.schemas import Choice, TestItem, Tests, Test

router = APIRouter(prefix="/tests", tags=["Тесты"])

@router.get("/finished_list/")
async def get_finished_list(
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (select(Tests.id, Test.title, Test.image, Tests.last_update).
            select_from(Tests).
            join(Test, Test.id == Tests.test_id).
            where(Tests.user_id == token.sub, Tests.ended == True))
    res = (await session.execute(stmt)).mappings().all()
    return res

@router.get("/unfinished_list/")
async def get_unfinished_list(
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (select(Tests.id, Test.title, Test.image, Tests.last_update).
            select_from(Tests).
            join(Test, Test.id == Tests.test_id).
            where(Tests.user_id == token.sub, Tests.ended == False))
    res = (await session.execute(stmt)).mappings().all()
    return res

@router.post("/{test_id}/start/")
async def start_tests(
    test_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    tests_service = TestsService(session)
    choice_service = ChoiceService(session)
    test_item_service = TestItemService(session)
    items = await test_item_service.list(test_item_service.schema.test_id == test_id)
    items = [int(i.id) for i in items]
    pair, items = ChoiceService.get_pair(items)
    tests = await tests_service.add(
        {"user_id": token.sub, "items": items, "test_id": test_id, "next_items": []}
    )
    await session.commit()
    await session.refresh(tests)
    tests_id = tests.id

    choice = await choice_service.add(
        {"tests_id": tests_id, "winner_id": pair[0], "loser_id": pair[1]}
    )
    await session.commit()
    await session.refresh(choice)
    choice_id = choice.id
    tests = await tests_service.patch(
        {"cur_choice": choice_id}, tests_service.schema.id == tests_id
    )
    await session.commit()
    return {"tests_id": tests_id}

@router.post("/{tests_id}/refresh/")
async def refresh(
    tests_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    tests_service = TestsService(session)
    choice_service = ChoiceService(session)
    test_item_service = TestItemService(session)
    tests = await tests_service.get(
        tests_service.schema.id == tests_id, tests_service.schema.user_id == token.sub
    )
    cur_choice = await choice_service.get(Choice.id == tests.cur_choice)
    items = [cur_choice.winner_id, cur_choice.loser_id] + list(tests.items)
    pair, items = ChoiceService.get_pair(items)
    cur_choice = await choice_service.patch({"winner_id": pair[0], "loser_id": pair[1]}, Choice.id == tests.cur_choice)
    tests = await tests_service.patch({"items": items}, tests_service.schema.id == tests_id)
    await session.commit()
    item1 = await test_item_service.get(
        test_item_service.schema.id == pair[0]
    )
    item2 = await test_item_service.get(
        test_item_service.schema.id == pair[1]
    )
    res = {
        "items": [
            {
                "id": pair[0],
                "videoId": item1.videoId,
                "title": item1.title,
            },
            {"id": pair[1], "videoId": item2.videoId, "title": item2.title},
        ],
    }
    return res

@router.post("/{tests_id}/rechoice/{winner_id}/")
async def make_rechoice(
    tests_id: int,
    winner_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    tests_service = TestsService(session)
    choice_service = ChoiceService(session)
    tests = await tests_service.get(
        tests_service.schema.id == tests_id, tests_service.schema.user_id == token.sub
    )
    if not tests:
        raise HTTPException(status_code=404, detail="Тест не найден")
    choice = await choice_service.get(Choice.id==tests.prev_choice)
    if choice.winner_id != winner_id:
        await choice_service.patch({"winner_id": choice.loser_id, "loser_id": choice.winner_id}, Choice.id==choice.id)
        await session.commit()
    return True
    
@router.post("/{tests_id}/choice/{winner_id}/")
async def make_choice(
    tests_id: int,
    winner_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    tests_service = TestsService(session)
    choice_service = ChoiceService(session)
    test_item_service = TestItemService(session)
    tests = await tests_service.get(
        tests_service.schema.id == tests_id, tests_service.schema.user_id == token.sub
    )
    if not tests:
        raise HTTPException(status_code=404, detail="Тест не найден")
    items = list(tests.items)
    next_items = list(tests.next_items)
    next_items.append(winner_id)
    cur_choice_id = int(tests.cur_choice)
    prev_choice_id = tests.prev_choice
    stage = int(tests.stage)
    cur_choice = await choice_service.get(choice_service.schema.id == cur_choice_id)
    if cur_choice.winner_id != winner_id:
        await choice_service.patch(
            {"winner_id": cur_choice.loser_id, "loser_id": cur_choice.winner_id},
            choice_service.schema.id == cur_choice_id,
        )
    pair, items = ChoiceService.get_pair(items)
    if len(pair) == 1:
        next_items.append(pair[0])

    if len(pair) < 2:
        if next_items is not None and len(next_items) == 1:
            await tests_service.patch(
                {
                    "ended": True,
                    "prev_choice": None,
                    "cur_choice": None,
                    "items": [],
                    "next_items": [],
                },
                tests.id == tests_id,
            )
            await session.commit()
            return {"ended": True}
        else:
            new_all_rounds = len(next_items) // 2
            new_pair, next_items = ChoiceService.get_pair(next_items)
            new_choice = await choice_service.add(
                {
                    "tests_id": tests_id,
                    "winner_id": new_pair[0],
                    "loser_id": new_pair[1],
                    "stage": stage + 1,
                }
            )
            await session.commit()
            await session.refresh(new_choice)
            new_choice_id = int(new_choice.id)
            await tests_service.patch(
                {
                    "prev_choice": None,
                    "cur_choice": new_choice_id,
                    "stage": stage + 1,
                    "items": next_items,
                    "next_items": [],
                    "is_refreshed": False
                },
                tests_service.schema.id == tests_id,
            )
            await session.commit()
            item1 = await test_item_service.get(
                test_item_service.schema.id == new_pair[0]
            )
            item2 = await test_item_service.get(
                test_item_service.schema.id == new_pair[1]
            )
            prev_choice = await choice_service.get(
                choice_service.schema.id == prev_choice_id
            )
            res = {
                "stage": stage + 1,
                "all_rounds": new_all_rounds,
                "items": [
                    {
                        "id": new_pair[0],
                        "videoId": item1.videoId,
                        "title": item1.title,
                    },
                    {"id": new_pair[1], "videoId": item2.videoId, "title": item2.title},
                ],
                "prev_items": None,
                "ended": False
            }
            return res
    new_choice = await choice_service.add(
        {
            "tests_id": tests_id,
            "winner_id": pair[0],
            "loser_id": pair[1],
            "stage": stage,
        }
    )
    await session.commit()
    await session.refresh(new_choice)
    new_choice_id = int(new_choice.id)
    await tests_service.patch(
        {
            "prev_choice": cur_choice_id,
            "cur_choice": new_choice_id,
            "items": items,
            "next_items": next_items,
            "is_refreshed": False
        },
        tests_service.schema.id == tests_id,
    )
    await session.commit()
    await session.refresh(tests)
    prev_choice = await choice_service.get(Choice.id == tests.prev_choice)
    item1 = await test_item_service.get(test_item_service.schema.id == pair[0])
    item2 = await test_item_service.get(test_item_service.schema.id == pair[1])
    res = {
        "items": [
            {
                "id": pair[0],
                "videoId": item1.videoId,
                "title": item1.title,
            },
            {"id": pair[1], "videoId": item2.videoId, "title": item2.title},
        ],
        "prev_items": None,
        "ended": False,
    }
    if prev_choice:
        prev_item1 = await test_item_service.get(
            test_item_service.schema.id == prev_choice.winner_id
        )
        prev_item2 = await test_item_service.get(
            test_item_service.schema.id == prev_choice.loser_id
        )
        res.update(
            {
                "prev_items": [
                    {
                        "id": prev_choice.winner_id,
                        "videoId": prev_item1.videoId,
                        "title": prev_item1.title,
                    },
                    {
                        "id": prev_choice.loser_id,
                        "videoId": prev_item2.videoId,
                        "title": prev_item2.title,
                    },
                ],
            }
        )
    return res


@router.get("/{tests_id}/")
async def get_tests(
    tests_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    tests_service = TestsService(session)
    tests = await tests_service.get(tests_service.schema.id == tests_id)
    if not tests or (tests.user_id != token.sub and not tests.ended):
        raise HTTPException(status_code=404, detail="Тест не найден")
    stage = tests.stage
    is_refreshed = tests.is_refreshed
    round = len(tests.next_items) + 1
    all_rounds = (len(tests.items) // 2) + round
    choice_service = ChoiceService(session)
    test_item_service = TestItemService(session)
    test_id = int(tests.test_id)
    if tests.ended:
        all_items = []
        stmt = (
            select(
                Choice.winner_id.label("id"),
                TestItem.videoId,
                TestItem.title,
            )
            .select_from(TestItem)
            .join(Choice, TestItem.id == Choice.winner_id)
            .where(
                TestItem.test_id == test_id,
                Choice.stage == stage,
                Choice.tests_id == tests_id,
            )
            .order_by(TestItem.id)
        )
        res = await session.execute(stmt)
        columns = res.keys()
        result_list = [dict(zip(columns, row)) for row in res]
        all_items += result_list
        for i in range(stage, 0, -1):
            stmt = (
                select(
                    Choice.loser_id.label("id"),
                    TestItem.videoId,
                    TestItem.title,
                )
                .select_from(TestItem)
                .join(Choice, TestItem.id == Choice.loser_id)
                .where(
                    TestItem.test_id == test_id,
                    Choice.stage == i,
                    Choice.tests_id == tests_id,
                )
                .order_by(TestItem.id)
            )
            res = await session.execute(stmt)
            columns = res.keys()
            result_list = [dict(zip(columns, row)) for row in res]
            all_items += result_list
        return {"items": all_items, "ended": True}
    cur_choice = await choice_service.get(choice_service.schema.id == tests.cur_choice)
    prev_choice = await choice_service.get(
        choice_service.schema.id == tests.prev_choice
    )
    item1 = await test_item_service.get(
        test_item_service.schema.id == cur_choice.winner_id
    )
    item2 = await test_item_service.get(
        test_item_service.schema.id == cur_choice.loser_id
    )
    res = {
        "items": [
            {
                "id": cur_choice.winner_id,
                "videoId": item1.videoId,
                "title": item1.title,
            },
            {"id": cur_choice.loser_id, "videoId": item2.videoId, "title": item2.title},
        ],
        "prev_items": None,
        "ended": False,
        "stage": stage,
        "round": round,
        "all_rounds": all_rounds,
        "is_refreshed": is_refreshed
    }
    if prev_choice:
        prev_item1 = await test_item_service.get(
            test_item_service.schema.id == prev_choice.winner_id
        )
        prev_item2 = await test_item_service.get(
            test_item_service.schema.id == prev_choice.loser_id
        )
        res.update(
            {
                "prev_items": [
                    {
                        "id": prev_choice.winner_id,
                        "videoId": prev_item1.videoId,
                        "title": prev_item1.title,
                    },
                    {
                        "id": prev_choice.loser_id,
                        "videoId": prev_item2.videoId,
                        "title": prev_item2.title,
                    },
                ],
            }
        )
    return res

@router.get("/{tests_id}/items/")
async def get_items(
    tests_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    tests_service = TestsService(session)
    tests = await tests_service.get(Tests.id == tests_id, Tests.user_id == token.sub)
    if not tests or tests.ended:
        raise HTTPException(status_code=404, detail="Тест не найден")
    stmt = (select(TestItem.videoId, TestItem.title)).select_from(TestItem).where(TestItem.id.in_(tests.items))
    items = await session.execute(stmt)
    items = items.mappings().all()
    return items

@router.get("/{tests_id}/winloss/{item_id}/")
async def get_winloss(
    tests_id: int,
    item_id: int,
    token: JwtTokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_async_session),
):
    tests_service = TestsService(session)

    tests = await tests_service.get(tests_service.schema.id == tests_id)
    if not tests or not tests.ended:
        raise HTTPException(status_code=404, detail="Тест не найден")

    stmt = (
        select(TestItem.videoId, TestItem.title)
        .select_from(Choice)
        .join(TestItem, TestItem.id == Choice.loser_id)
        .where(Choice.tests_id == tests_id, Choice.winner_id == item_id)
    )
    res = session.execute(stmt)
    res = await session.execute(stmt)
    columns = res.keys()
    wins = [dict(zip(columns, row)) for row in res]

    stmt = (
        select(TestItem.videoId, TestItem.title)
        .select_from(Choice)
        .join(TestItem, TestItem.id == Choice.winner_id)
        .where(Choice.tests_id == tests_id, Choice.loser_id == item_id)
    )
    res = session.execute(stmt)
    res = await session.execute(stmt)
    columns = res.keys()
    losses = [dict(zip(columns, row)) for row in res]

    return {"wins": wins, "losses": losses}
