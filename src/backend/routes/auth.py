"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import Optional
import logging

from config import settings
from auth.utils import create_access_token, verify_token, hash_token, generate_refresh_token
from auth.db import (
    get_user_by_github_id,
    create_user,
    update_user,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    get_db_session,
)
from auth.github import GitHubOAuthService
from auth.schemas import (
    TokenResponse,
    UserResponse,
    CurrentUserResponse,
    RefreshTokenRequest,
)
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_current_user(request: Request, db: Session = Depends(get_db_session)) -> User:
    """Dependency to get current authenticated user"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Import here to avoid circular imports
        from auth.db import get_user_by_id
        user = get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/github")
async def github_login():
    """Initiate GitHub OAuth flow"""
    try:
        url, state = GitHubOAuthService.get_authorization_url()
        return {"url": url, "state": state}
    except Exception as e:
        logger.error(f"Error initiating GitHub OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate GitHub login")


@router.post("/github/callback")
async def github_callback(
    code: str,
    state: str,
    response: Response,
    db: Session = Depends(get_db_session)
):
    """Handle GitHub OAuth callback"""
    try:
        # Exchange code for access token
        access_token = await GitHubOAuthService.exchange_code_for_token(code)
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        # Get user information from GitHub
        user_info = await GitHubOAuthService.get_user_info(access_token)
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get GitHub user information")
        
        # Check if user exists
        user = get_user_by_github_id(db, user_info["github_id"])
        
        if not user:
            # Create new user
            user = create_user(
                db,
                github_id=user_info["github_id"],
                username=user_info["username"],
                email=user_info["email"],
                display_name=user_info["display_name"],
                avatar_url=user_info["avatar_url"],
            )
            logger.info(f"Created new user: {user.username}")
        else:
            # Update existing user
            user = update_user(
                db,
                user,
                display_name=user_info["display_name"],
                avatar_url=user_info["avatar_url"],
            )
            logger.info(f"Updated user: {user.username}")
        
        # Generate tokens
        access_token_jwt = create_access_token({"sub": user.id, "email": user.email})
        refresh_token_str = generate_refresh_token()
        refresh_token_hash = hash_token(refresh_token_str)
        
        # Store refresh token in database
        create_refresh_token(db, user.id, refresh_token_hash)
        
        # Set refresh token as HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token_str,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 60 * 60,
        )
        
        return {
            "user": UserResponse.from_orm(user),
            "access_token": access_token_jwt,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRATION_MINUTES * 60,
        }
    except Exception as e:
        logger.error(f"Error in GitHub callback: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    """Get current user information"""
    # This is a placeholder - full token response would be generated during login
    return {
        "user": UserResponse.from_orm(current_user),
        "token": TokenResponse(
            access_token="",  # Token is already verified in dependency
            refresh_token="",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        ),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: Request,
    db: Session = Depends(get_db_session)
) -> TokenResponse:
    """Refresh access token using refresh token from cookie"""
    try:
        # Get refresh token from cookie
        refresh_token_str = request.cookies.get("refresh_token")
        
        if not refresh_token_str:
            raise HTTPException(status_code=401, detail="Refresh token not found")
        
        # Verify refresh token format
        refresh_token_hash = hash_token(refresh_token_str)
        
        # Get the token from database to verify it's valid
        # We need to find the user first - this is a limitation, ideally we'd store user_id in the token
        # For now, we'll need to check all users' tokens
        from sqlalchemy import func
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token_hash == refresh_token_hash
        ).first()
        
        if not token_record or not verify_refresh_token(db, refresh_token_hash, token_record.user_id):
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        # Get user
        from auth.db import get_user_by_id
        user = get_user_by_id(db, token_record.user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Generate new access token
        access_token_jwt = create_access_token({"sub": user.id, "email": user.email})
        
        return TokenResponse(
            access_token=access_token_jwt,
            refresh_token=refresh_token_str,
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)) -> dict:
    """Logout user"""
    # Clear refresh token cookie
    response.delete_cookie("refresh_token")
    
    return {"message": "Logged out successfully"}
