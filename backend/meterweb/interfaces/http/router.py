from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from meterweb.application.dto import BuildingCreateDTO, LoginDTO
from meterweb.application.use_cases import (
    CreateBuildingUseCase,
    ListBuildingsUseCase,
    LoginUseCase,
)
from meterweb.domain.auth import AuthenticationError
from meterweb.interfaces.http.dependencies import (
    get_create_building_use_case,
    get_list_buildings_use_case,
    get_login_use_case,
)
from meterweb.interfaces.http.schemas import (
    BuildingCreateRequest,
    BuildingResponse,
)

templates = Jinja2Templates(directory="meterweb/templates")
router = APIRouter()


def _require_auth(request: Request) -> str:
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return username


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    try:
        use_case.execute(LoginDTO(username=username, password=password))
    except AuthenticationError:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Ungültige Zugangsdaten."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.session["username"] = username
    return RedirectResponse(url="/buildings", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/buildings")
def buildings_page(
    request: Request,
    list_use_case: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
):
    _require_auth(request)
    buildings = list_use_case.execute()
    return templates.TemplateResponse(
        request,
        "buildings.html",
        {"buildings": buildings, "error": None},
    )


@router.post("/buildings")
def create_building_submit(
    request: Request,
    name: str = Form(),
    create_use_case: CreateBuildingUseCase = Depends(get_create_building_use_case),
    list_use_case: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
):
    _require_auth(request)
    try:
        create_use_case.execute(BuildingCreateDTO(name=name))
        return RedirectResponse(url="/buildings", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as err:
        buildings = list_use_case.execute()
        return templates.TemplateResponse(
            request,
            "buildings.html",
            {"buildings": buildings, "error": str(err)},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/api/v1/buildings", response_model=list[BuildingResponse], tags=["buildings"])
def list_buildings_api(
    request: Request,
    list_use_case: ListBuildingsUseCase = Depends(get_list_buildings_use_case),
):
    _require_auth(request)
    return [BuildingResponse(id=str(item.id), name=item.name) for item in list_use_case.execute()]


@router.post("/api/v1/buildings", response_model=BuildingResponse, tags=["buildings"])
def create_building_api(
    request: Request,
    payload: BuildingCreateRequest,
    create_use_case: CreateBuildingUseCase = Depends(get_create_building_use_case),
):
    _require_auth(request)
    try:
        created = create_use_case.execute(BuildingCreateDTO(name=payload.name))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return BuildingResponse(id=str(created.id), name=created.name)
