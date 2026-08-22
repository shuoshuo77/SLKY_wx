"""Public homepage content and platform-admin maintenance endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.home import Banner, FeaturedService
from app.models.other import IndustryData
from app.models.user import User
from app.schemas.home import (
    BannerCreate,
    BannerOut,
    BannerUpdate,
    FeaturedServiceCreate,
    FeaturedServiceOut,
    FeaturedServiceUpdate,
    HomePageOut,
)


router = APIRouter(prefix="/api/home", tags=["homepage"])


def _active_banners(db: Session) -> list[Banner]:
    now = datetime.now()
    return db.query(Banner).filter(
        Banner.is_active == True,
        or_(Banner.starts_at.is_(None), Banner.starts_at <= now),
        or_(Banner.ends_at.is_(None), Banner.ends_at >= now),
    ).order_by(Banner.sort_order.asc(), Banner.id.asc()).all()


@router.get("", response_model=HomePageOut, summary="Homepage content")
def get_homepage(db: Session = Depends(get_db)):
    services = db.query(FeaturedService).filter(
        FeaturedService.is_active == True,
    ).order_by(FeaturedService.sort_order.asc(), FeaturedService.id.asc()).all()
    metrics = db.query(IndustryData).filter(
        IndustryData.status == "published",
        IndustryData.metric_value.isnot(None),
    ).order_by(IndustryData.sort_order.asc(), IndustryData.id.asc()).limit(12).all()
    return HomePageOut(
        banners=[BannerOut.model_validate(item) for item in _active_banners(db)],
        featured_services=[FeaturedServiceOut.model_validate(item) for item in services],
        industry_metrics=metrics,
    )


@router.get("/banners", response_model=list[BannerOut], summary="Active banners")
def list_banners(db: Session = Depends(get_db)):
    return _active_banners(db)


@router.get("/featured-services", response_model=list[FeaturedServiceOut], summary="Active featured services")
def list_featured_services(db: Session = Depends(get_db)):
    return db.query(FeaturedService).filter(
        FeaturedService.is_active == True,
    ).order_by(FeaturedService.sort_order.asc(), FeaturedService.id.asc()).all()


@router.post("/banners", response_model=BannerOut, status_code=201, summary="Create banner")
def create_banner(
    request: BannerCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    banner = Banner(created_by=admin.id, **request.model_dump())
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


@router.put("/banners/{banner_id}", response_model=BannerOut, summary="Update banner")
def update_banner(
    banner_id: int,
    request: BannerUpdate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(banner, field, value)
    db.commit()
    db.refresh(banner)
    return banner


@router.delete("/banners/{banner_id}", summary="Delete banner")
def delete_banner(
    banner_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found")
    db.delete(banner)
    db.commit()
    return {"message": "Banner deleted"}


@router.post("/featured-services", response_model=FeaturedServiceOut, status_code=201, summary="Create featured service")
def create_featured_service(
    request: FeaturedServiceCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = FeaturedService(created_by=admin.id, **request.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/featured-services/{service_id}", response_model=FeaturedServiceOut, summary="Update featured service")
def update_featured_service(
    service_id: int,
    request: FeaturedServiceUpdate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = db.query(FeaturedService).filter(FeaturedService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Featured service not found")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/featured-services/{service_id}", summary="Delete featured service")
def delete_featured_service(
    service_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = db.query(FeaturedService).filter(FeaturedService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Featured service not found")
    db.delete(service)
    db.commit()
    return {"message": "Featured service deleted"}
