"""
GitHub OAuth service
"""
import httpx
from config import settings
from auth.utils import create_github_oauth_state
import logging

logger = logging.getLogger(__name__)


class GitHubOAuthService:
    """Service for GitHub OAuth interactions"""

    GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"
    GITHUB_USER_EMAILS_URL = "https://api.github.com/user/emails"

    @staticmethod
    def get_authorization_url() -> tuple[str, str]:
        """Get GitHub OAuth authorization URL and state token"""
        state = create_github_oauth_state()
        
        url = f"{GitHubOAuthService.GITHUB_AUTHORIZE_URL}?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_OAUTH_REDIRECT_URI}&scope=user:email&state={state}"
        
        return url, state

    @staticmethod
    async def exchange_code_for_token(code: str) -> str | None:
        """Exchange authorization code for access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GitHubOAuthService.GITHUB_TOKEN_URL,
                    params={
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
                    },
                    headers={"Accept": "application/json"},
                )

                if response.status_code != 200:
                    logger.error(f"GitHub token exchange failed: {response.text}")
                    return None

                data = response.json()
                return data.get("access_token")
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None

    @staticmethod
    async def get_user_info(access_token: str) -> dict | None:
        """Get GitHub user information"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

                # Get user profile
                user_response = await client.get(
                    GitHubOAuthService.GITHUB_USER_URL,
                    headers=headers,
                )

                if user_response.status_code != 200:
                    logger.error(f"Failed to get GitHub user info: {user_response.text}")
                    return None

                user_data = user_response.json()

                # Get user emails (to find primary email)
                emails_response = await client.get(
                    GitHubOAuthService.GITHUB_USER_EMAILS_URL,
                    headers=headers,
                )

                email = user_data.get("email")
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    # Find primary email
                    for email_obj in emails:
                        if email_obj.get("primary"):
                            email = email_obj.get("email")
                            break

                return {
                    "github_id": str(user_data.get("id")),
                    "username": user_data.get("login"),
                    "email": email or f"{user_data.get('login')}@github.com",
                    "display_name": user_data.get("name") or user_data.get("login"),
                    "avatar_url": user_data.get("avatar_url"),
                }
        except Exception as e:
            logger.error(f"Error fetching GitHub user info: {e}")
            return None
