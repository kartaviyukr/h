import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.schemas.menu import MenuDetail, MenuGenerateIn, MenuListItem, MenuOut
from app.services.menu_service import MenuGenerationError, MenuService

router = APIRouter(prefix="/menu", tags=["menu"])


def _to_detail(menu) -> MenuDetail:
    return MenuDetail(
        id=menu.id,
        title=menu.title,
        days_count=menu.days_count,
        adjusted=menu.adjusted,
        created_at=menu.created_at,
        menu=MenuOut.model_validate(menu.payload),
    )


@router.post("/generate", response_model=MenuDetail)
def generate_menu(payload: MenuGenerateIn, user: CurrentUser, session: SessionDep) -> MenuDetail:
    try:
        menu, _ = MenuService(session).generate(user.id, payload)
    except MenuGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Menu generation failed: {exc}",
        ) from exc
    return _to_detail(menu)


@router.get("", response_model=list[MenuListItem])
def list_menus(user: CurrentUser, session: SessionDep) -> list[MenuListItem]:
    menus = MenuService(session).list(user.id)
    return [MenuListItem.model_validate(m) for m in menus]


@router.get("/{menu_id}", response_model=MenuDetail)
def get_menu(menu_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> MenuDetail:
    menu = MenuService(session).get(user.id, menu_id)
    if menu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    return _to_detail(menu)
