import json
import uuid

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.integrations.deepseek import DeepSeekError, generate_menu_json
from app.models.menu import Menu
from app.models.profile import Profile
from app.repositories.menu_repo import MenuRepository
from app.repositories.profile_repo import ProfileRepository
from app.schemas.menu import MenuGenerateIn, MenuOut
from app.services.nutrition import correct_macros

_SYSTEM_PROMPT = (
    "Ты — нутрициолог-составитель меню. Отвечай СТРОГО валидным JSON-объектом "
    "без markdown и пояснений. Все тексты (названия блюд, ингредиенты, шаги) — "
    "на русском языке. Структура JSON:\n"
    '{"days_count": int, '
    '"total_per_day": {"kcal": num, "protein_g": num, "fat_g": num, "carbs_g": num}, '
    '"days": [{"day_index": int, '
    '"totals": {"kcal": num, "protein_g": num, "fat_g": num, "carbs_g": num}, '
    '"meals": [{"type": "breakfast|lunch|dinner|snack", "title": str, '
    '"ingredients": [{"name": str, "amount": num, "unit": str}], '
    '"steps": [str], '
    '"macros": {"kcal": num, "protein_g": num, "fat_g": num, "carbs_g": num}, '
    '"est_cost_rub": num}]}]}'
)


class MenuGenerationError(Exception):
    """Raised when the LLM output cannot be produced or validated."""


def _build_user_prompt(profile: Profile | None, request: MenuGenerateIn) -> str:
    lines = [f"Составь меню на {request.days_count} дн."]
    meals = "завтрак, обед, ужин"
    if request.include_snacks:
        meals += " и 1–2 перекуса"
    lines.append(f"Приёмы пищи каждый день: {meals}.")

    if profile:
        if profile.goal:
            lines.append(f"Цель пользователя: {profile.goal}.")
        targets = []
        if profile.target_kcal:
            targets.append(f"{profile.target_kcal} ккал")
        if profile.target_protein_g:
            targets.append(f"белки {profile.target_protein_g} г")
        if profile.target_fat_g:
            targets.append(f"жиры {profile.target_fat_g} г")
        if profile.target_carbs_g:
            targets.append(f"углеводы {profile.target_carbs_g} г")
        if targets:
            lines.append("Целевые КБЖУ в день: " + ", ".join(targets) + ".")
        if profile.allergies:
            lines.append(
                "Полностью исключи продукты (аллергии/исключения): "
                + ", ".join(profile.allergies)
                + "."
            )
        if profile.budget_rub and profile.budget_period:
            lines.append(
                f"Ориентируйся на бюджет {profile.budget_rub} руб. за {profile.budget_period}."
            )

    if request.note:
        lines.append(f"Дополнительно: {request.note}")

    lines.append("Укажи граммовки ингредиентов и КБЖУ каждого приёма пищи.")
    return "\n".join(lines)


class MenuService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.menus = MenuRepository(session)
        self.profiles = ProfileRepository(session)

    def generate(self, user_id: uuid.UUID, request: MenuGenerateIn) -> tuple[Menu, bool]:
        profile = self.profiles.get(user_id)
        system_prompt = _SYSTEM_PROMPT
        user_prompt = _build_user_prompt(profile, request)

        try:
            raw = generate_menu_json(system_prompt, user_prompt)
            menu_out = MenuOut.model_validate(raw)
        except (DeepSeekError, ValidationError, json.JSONDecodeError) as exc:
            raise MenuGenerationError(str(exc)) from exc

        adjusted = correct_macros(menu_out, profile)
        title = f"Меню на {menu_out.days_count} дн."
        params = {
            "days_count": request.days_count,
            "include_snacks": request.include_snacks,
            "note": request.note,
            "target_kcal": profile.target_kcal if profile else None,
        }
        menu = self.menus.create(
            user_id=user_id,
            title=title,
            days_count=menu_out.days_count,
            adjusted=adjusted,
            params=params,
            payload=menu_out.model_dump(mode="json"),
        )
        self.session.commit()
        return menu, adjusted

    def get(self, user_id: uuid.UUID, menu_id: uuid.UUID) -> Menu | None:
        return self.menus.get_for_user(user_id, menu_id)

    def list(self, user_id: uuid.UUID):
        return self.menus.list_for_user(user_id)
