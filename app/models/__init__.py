from app.models.base import Base
from app.models.user import User
from app.models.auth import (
    UserIdentity,
    AuthSession,
    TrustedDevice,
    OtpChallenge,
    PasswordReset,
)
from app.models.rbac import Role, Permission, UserRole, RolePermission
from app.models.curriculum import Language, Level, Unit, Lesson
from app.models.lesson_engine import (
    LessonItem,
    LessonItemChoice,
    UserLessonProgress,
    LessonAttempt,
)
from app.models.vocabulary import (
    Lexeme,
    WordSense,
    WordExample,
    LessonLexeme,
    UserLexemeState,
    UserWordError,
)

from app.features.review.model import ReviewAttempt, UserReviewSettings

__all__ = [
    "Base",
    "User",
    "UserIdentity",
    "AuthSession",
    "TrustedDevice",
    "OtpChallenge",
    "PasswordReset",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "Language",
    "Level",
    "Unit",
    "Lesson",
    "LessonItem",
    "LessonItemChoice",
    "UserLessonProgress",
    "LessonAttempt",
    "Lexeme",
    "WordSense",
    "WordExample",
    "LessonLexeme",
    "UserLexemeState",
    "UserWordError",
    "ReviewAttempt",
    "UserReviewSettings",
]
