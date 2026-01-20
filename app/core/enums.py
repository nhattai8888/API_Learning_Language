import enum

class UserSegment(str, enum.Enum):
    TEEN = "TEEN"
    WORKING = "WORKING"
    GENERAL = "GENERAL"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"

class IdentityType(str, enum.Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"

class IdentityStatus(str, enum.Enum):
    PENDING_VERIFY = "PENDING_VERIFY"
    VERIFIED = "VERIFIED"
    DISABLED = "DISABLED"

class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class OtpPurpose(str, enum.Enum):
    LOGIN_2FA = "LOGIN_2FA"
    VERIFY_PHONE = "VERIFY_PHONE"
    RESET_PASSWORD = "RESET_PASSWORD"

class OtpStatus(str, enum.Enum):
    CREATED = "CREATED"
    SENT = "SENT"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    LOCKED = "LOCKED"

class OtpChannel(str, enum.Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"

class ResetStatus(str, enum.Enum):
    PENDING = "PENDING"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class EntityStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"

class LessonType(str, enum.Enum):
    STANDARD = "STANDARD"
    BOSS = "BOSS"
    REVIEW = "REVIEW"

class PublishStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class LessonItemType(str, enum.Enum):
    MCQ = "MCQ"
    CLOZE = "CLOZE"
    MATCH = "MATCH"
    REORDER = "REORDER"
    LISTEN = "LISTEN"
    SPEAK = "SPEAK"

class LessonProgressStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class AttemptStatus(str, enum.Enum):
    STARTED = "STARTED"
    SUBMITTED = "SUBMITTED"
    PENDING_AI = "PENDING_AI"

class WordPOS(str, enum.Enum):
    NOUN = "NOUN"
    VERB = "VERB"
    ADJ = "ADJ"
    ADV = "ADV"
    PREP = "PREP"
    PHRASE = "PHRASE"

class WordMastery(str, enum.Enum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    KNOWN = "KNOWN"
    MASTERED = "MASTERED"

class WordFormType(str, enum.Enum):
    INFLECTION = "INFLECTION"
    VARIANT = "VARIANT"

class WordDomain(str, enum.Enum):
    DAILY = "DAILY"
    ACADEMIC = "ACADEMIC"
    BUSINESS = "BUSINESS"

import enum

class EntityStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"

class LexemeType(str, enum.Enum):
    NOUN = "NOUN"
    VERB = "VERB"
    ADJ = "ADJ"
    ADV = "ADV"
    PREP = "PREP"
    PHRASE = "PHRASE"
    OTHER = "OTHER"

class PublishStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class WordDomain(str, enum.Enum):
    DAILY = "DAILY"
    ACADEMIC = "ACADEMIC"
    BUSINESS = "BUSINESS"
    TRAVEL = "TRAVEL"
    TECH = "TECH"
    OTHER = "OTHER"

class WordMastery(str, enum.Enum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    KNOWN = "KNOWN"
    MASTERED = "MASTERED"

class WordErrorType(str, enum.Enum):
    PRONUNCIATION = "PRONUNCIATION"
    STRESS = "STRESS"
    INTONATION = "INTONATION"
    MEANING = "MEANING"
    SPELLING = "SPELLING"
    GRAMMAR = "GRAMMAR"
    COLLOCATION = "COLLOCATION"
    OTHER = "OTHER"

class WordErrorSource(str, enum.Enum):
    SPEAKING = "SPEAKING"
    LISTENING = "LISTENING"
    READING = "READING"
    WRITING = "WRITING"
    QUIZ = "QUIZ"
    OTHER = "OTHER"

class Severity(str, enum.Enum):
    GOOD = "GOOD"
    OK = "OK"
    BAD = "BAD"
