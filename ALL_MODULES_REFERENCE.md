# ALL MODULES - Comprehensive API Reference

## Module 1: AUTH (Already Detailed in AUTH_MODULES_SUMMARY.md)

### Summary
- 11 endpoints
- Authentication (email, phone OTP)
- Token management (access, refresh)
- **New:** Biometric login + Trusted device
- **New:** Forgot password + Reset password

---

## Module 2: RBAC (Role-Based Access Control)

### Endpoints

#### 1. Create Role
**Path:** `POST /rbac/roles`  
**Auth Required:** Yes (permission: `ROLE_MANAGE`)  
**Request Schema:** `RoleCreate`
- `code: str` (required)
- `name: str` (required)

**Response:** `ApiResponse[RoleOut]`
- `id: str`
- `code: str`
- `name: str`
- `status: str`

#### 2. List Roles
**Path:** `GET /rbac/roles`  
**Auth Required:** Yes (permission: `ROLE_MANAGE`)  
**Response:** `ApiResponse[list[RoleOut]]`

#### 3. Create Permission
**Path:** `POST /rbac/permissions`  
**Auth Required:** Yes (permission: `ROLE_MANAGE`)  
**Request Schema:** `PermissionCreate`
- `code: str` (required)
- `module: str` (required)
- `description: Optional[str]`

**Response:** `ApiResponse[PermissionOut]`
- `id: str`
- `code: str`
- `module: str`
- `description: Optional[str]`
- `status: str`

#### 4. List Permissions
**Path:** `GET /rbac/permissions`  
**Auth Required:** Yes (permission: `ROLE_MANAGE`)  
**Response:** `ApiResponse[list[PermissionOut]]`

#### 5. Assign Roles to User
**Path:** `POST /rbac/assign-roles`  
**Auth Required:** Yes (permission: `USER_MANAGE`)  
**Request Schema:** `AssignRoleRequest`
- `user_id: str` (required)
- `role_codes: List[str]` (required)

**Response:** `ApiResponse[dict]`
- `user_id: str`
- `roles: List[str]`

#### 6. Assign Permissions to Role
**Path:** `POST /rbac/assign-permissions`  
**Auth Required:** Yes (permission: `ROLE_MANAGE`)  
**Request Schema:** `AssignPermissionToRoleRequest`
- `role_code: str` (required)
- `permission_codes: List[str]` (required)

**Response:** `ApiResponse[dict]`
- `role: str`
- `permissions: List[str]`

---

## Module 3: CURRICULUM

### Sub-Resources: Languages, Levels, Units, Lessons

#### 1. Create Language
**Path:** `POST /curriculum/languages`  
**Auth Required:** Yes (permission: `LESSON_CREATE`)  
**Request Schema:** `LanguageCreate`
- `code: str` (min_length=2, max_length=10, required)
- `name: str` (min_length=2, max_length=50, required)
- `script: Optional[str]` (max_length=20)

**Response:** `ApiResponse[LanguageOut]`
- `id: UUID`
- `code: str`
- `name: str`
- `script: Optional[str]`

#### 2. Update Language
**Path:** `PATCH /curriculum/languages/{language_id}`  
**Auth Required:** Yes (permission: `LESSON_UPDATE`)  
**Request Schema:** `LanguageUpdate`
- `name: Optional[str]`
- `script: Optional[str]`

**Response:** `ApiResponse[LanguageOut]`

#### 3. List Languages
**Path:** `GET /curriculum/languages`  
**Response:** `ApiResponse[list[LanguageOut]]`

#### 4. Get Language
**Path:** `GET /curriculum/languages/{language_id}`  
**Response:** `ApiResponse[LanguageOut]`

#### 5. Create Level
**Path:** `POST /curriculum/levels`  
**Auth Required:** Yes (permission: `LESSON_CREATE`)  
**Request Schema:** `LevelCreate`
- `language_id: UUID` (required)
- `code: str` (min_length=1, max_length=20, required)
- `name: str` (min_length=1, max_length=50, required)
- `sort_order: int = 0`

**Response:** `ApiResponse[LevelOut]`

#### 6. Update Level
**Path:** `PATCH /curriculum/levels/{level_id}`  
**Auth Required:** Yes (permission: `LESSON_UPDATE`)  
**Request Schema:** `LevelUpdate`
- `name: Optional[str]`
- `sort_order: Optional[int]`

**Response:** `ApiResponse[LevelOut]`

#### 7. List Levels
**Path:** `GET /curriculum/levels/by-language/{language_id}`  
**Response:** `ApiResponse[list[LevelOut]]`

#### 8. Create Unit
**Path:** `POST /curriculum/units`  
**Auth Required:** Yes (permission: `LESSON_CREATE`)  
**Request Schema:** `UnitCreate`
- `language_id: UUID` (required)
- `level_id: Optional[UUID]`
- `title: str` (min_length=2, max_length=120, required)
- `description: Optional[str]`
- `sort_order: int = 0`

**Response:** `ApiResponse[UnitOut]`

#### 9. Update Unit
**Path:** `PATCH /curriculum/units/{unit_id}`  
**Auth Required:** Yes (permission: `LESSON_UPDATE`)  
**Request Schema:** `UnitUpdate`
- `level_id: Optional[UUID]`
- `title: Optional[str]`
- `description: Optional[str]`
- `sort_order: Optional[int]`

**Response:** `ApiResponse[UnitOut]`

#### 10. List Units
**Path:** `GET /curriculum/units/by-language/{language_id}?level_id={level_id}`  
**Query Params:**
- `level_id: Optional[str]`

**Response:** `ApiResponse[list[UnitOut]]`

#### 11. Create Lesson
**Path:** `POST /curriculum/lessons`  
**Auth Required:** Yes (permission: `LESSON_CREATE`)  
**Request Schema:** `LessonCreate`
- `language_id: UUID` (required)
- `unit_id: Optional[UUID]`
- `title: str` (min_length=2, max_length=120, required)
- `objective: Optional[str]`
- `estimated_minutes: int = 6`
- `lesson_type: LessonType = STANDARD`
- `slug: str` (min_length=2, max_length=160, required)
- `sort_order: int = 0`

**Response:** `ApiResponse[LessonOut]`
- `id: UUID`
- `language_id: UUID`
- `unit_id: Optional[UUID]`
- `title: str`
- `objective: Optional[str]`
- `estimated_minutes: int`
- `lesson_type: LessonType` (STANDARD | BOSS | REVIEW)
- `publish_status: PublishStatus` (DRAFT | REVIEW | PUBLISHED | ARCHIVED)
- `version: int`
- `slug: str`
- `sort_order: int`

#### 12. Update Lesson
**Path:** `PATCH /curriculum/lessons/{lesson_id}`  
**Auth Required:** Yes (permission: `LESSON_UPDATE`)  
**Request Schema:** `LessonUpdate`
- `unit_id: Optional[UUID]`
- `title: Optional[str]`
- `objective: Optional[str]`
- `estimated_minutes: Optional[int]`
- `lesson_type: Optional[LessonType]`
- `publish_status: Optional[PublishStatus]`
- `sort_order: Optional[int]`

**Response:** `ApiResponse[LessonOut]`

#### 13. List Lessons
**Path:** `GET /curriculum/lessons/by-language/{language_id}`  
**Query Params:**
- `unit_id: Optional[str]`
- `limit: int = 50`
- `offset: int = 0`

**Response:** `ApiResponse[list[LessonOut]]`

#### 14. Get Lesson
**Path:** `GET /curriculum/lessons/{lesson_id}`  
**Response:** `ApiResponse[LessonOut]`

---

## Module 4: VOCABULARY

### Sub-Resources: Lexemes, Senses, Examples, SRS Review, Weak Words

#### 1. Create Lexeme
**Path:** `POST /vocab/lexemes`  
**Auth Required:** Yes (permission: `VOCAB_LEXEME_CREATE`)  
**Request Schema:** `LexemeCreate`
- `language_id: UUID` (required)
- `type: LexemeType` (NOUN | VERB | ADJ | ADV | PREP | PHRASE | OTHER, required)
- `lemma: str` (min_length=1, max_length=180, required)
- `phoenic: Optional[str]`
- `audio_url: Optional[str]`
- `difficulty: int` (default=1, 1-10)
- `tags: Optional[Dict[str, Any]]`

**Response:** `ApiResponse[LexemeOut]`
- `id: UUID`
- `language_id: UUID`
- `type: LexemeType`
- `lemma: str`
- `phoenic: Optional[str]`
- `audio_url: Optional[str]`
- `difficulty: int`
- `tags: Optional[Dict]`
- `status: EntityStatus`
- `created_at: datetime`
- `updated_at: datetime`

#### 2. Update Lexeme
**Path:** `PATCH /vocab/lexemes/{lexeme_id}`  
**Auth Required:** Yes (permission: `VOCAB_LEXEME_UPDATE`)  
**Request Schema:** `LexemeUpdate`
- `type: Optional[LexemeType]`
- `lemma: Optional[str]`
- `phoenic: Optional[str]`
- `audio_url: Optional[str]`
- `difficulty: Optional[int]`
- `tags: Optional[Dict]`
- `status: Optional[EntityStatus]`

**Response:** `ApiResponse[LexemeOut]`

#### 3. Get Lexeme
**Path:** `GET /vocab/lexemes/{lexeme_id}`  
**Auth Required:** Yes (permission: `VOCAB_LEXEME_READ`)  
**Response:** `ApiResponse[LexemeOut]`

#### 4. List Lexemes
**Path:** `GET /vocab/lexemes?language_id={id}&q={query}&limit=50&offset=0`  
**Auth Required:** Yes (permission: `VOCAB_LEXEME_READ`)  
**Query Params:**
- `language_id: str` (required)
- `q: Optional[str]` (search query)
- `limit: int = 50`
- `offset: int = 0`

**Response:** `ApiResponse[list[LexemeOut]]`

#### 5. Create Sense
**Path:** `POST /vocab/senses`  
**Auth Required:** Yes (permission: `VOCAB_SENSE_CREATE`)  
**Request Schema:** `SenseCreate`
- `lexeme_id: UUID` (required)
- `sense_index: int = 1`
- `definition: str` (required)
- `domain: WordDomain = OTHER` (DAILY | ACADEMIC | BUSINESS | TRAVEL | TECH | OTHER)
- `cefr_level: Optional[str]`
- `translations: Optional[Dict]`
- `collocations: Optional[Dict]`
- `status: PublishStatus = DRAFT`

**Response:** `ApiResponse[SenseOut]`
- `id: UUID`
- `lexeme_id: UUID`
- `sense_index: int`
- `definition: str`
- `domain: WordDomain`
- `cefr_level: Optional[str]`
- `translations: Optional[Dict]`
- `collocations: Optional[Dict]`
- `status: PublishStatus`
- `created_at: datetime`
- `updated_at: datetime`

#### 6. Update Sense
**Path:** `PATCH /vocab/senses/{sense_id}`  
**Auth Required:** Yes (permission: `VOCAB_SENSE_UPDATE`)  
**Request Schema:** `SenseUpdate`
- All fields optional

**Response:** `ApiResponse[SenseOut]`

#### 7. List Senses by Lexeme
**Path:** `GET /vocab/senses/by-lexeme/{lexeme_id}`  
**Auth Required:** Yes (permission: `VOCAB_SENSE_READ`)  
**Response:** `ApiResponse[list[SenseOut]]`

#### 8. Create Example
**Path:** `POST /vocab/examples`  
**Auth Required:** Yes (permission: `VOCAB_EXAMPLE_CREATE`)  
**Request Schema:** `ExampleCreate`
- `sense_id: UUID` (required)
- `sentence: str` (required)
- `translation: Optional[Dict]`
- `audio_url: Optional[str]`
- `difficulty: int` (default=1, 1-10)
- `tags: Optional[Dict]`

**Response:** `ApiResponse[ExampleOut]`
- `id: UUID`
- `sense_id: UUID`
- `sentence: str`
- `translation: Optional[Dict]`
- `audio_url: Optional[str]`
- `difficulty: int`
- `tags: Optional[Dict]`
- `created_at: datetime`

#### 9. Update Example
**Path:** `PATCH /vocab/examples/{example_id}`  
**Auth Required:** Yes (permission: `VOCAB_EXAMPLE_UPDATE`)  
**Request Schema:** `ExampleUpdate`

**Response:** `ApiResponse[ExampleOut]`

#### 10. List Examples by Sense
**Path:** `GET /vocab/examples/by-sense/{sense_id}?limit=20`  
**Auth Required:** Yes (permission: `VOCAB_EXAMPLE_READ`)  
**Query Params:**
- `limit: int = 20`

**Response:** `ApiResponse[list[ExampleOut]]`

#### 11. Attach Lexemes to Lesson
**Path:** `POST /vocab/lessons/attach`  
**Auth Required:** Yes (permission: `VOCAB_LESSON_ATTACH`)  
**Request Schema:** `AttachLexemesToLessonRequest`
- `lesson_id: UUID` (required)
- `lexemes: List[Dict]` (required) - `[{lexeme_id, is_core, sort_order}]`

**Response:** `ApiResponse[list[LessonLexemeOut]]`
- `lesson_id: UUID`
- `lexeme_id: UUID`
- `is_core: bool`
- `sort_order: int`

#### 12. Get Today's SRS Review
**Path:** `GET /vocab/review/today`  
**Auth Required:** Yes  
**Response:** `ApiResponse[ReviewTodayResponse]`
- `items: List[ReviewCard]`
  - `lexeme: LexemeOut`
  - `senses: List[SenseOut]`
  - `examples: List[ExampleOut]`
  - `state: Dict[str, Any]` (SRS state: familiarity, mastery, next_review_at)
- `total: int`

#### 13. Submit SRS Review Result
**Path:** `POST /vocab/review/result`  
**Auth Required:** Yes  
**Request Schema:** `ReviewResultRequest`
- `lexeme_id: UUID` (required)
- `rating: int` (0-5, required) - 0=fail, 5=perfect
- `source: WordErrorSource` (SPEAKING | LISTENING | READING | WRITING | QUIZ | OTHER)

**Response:** `ApiResponse[dict]` (SRS state update result)

#### 14. Get Weak Words
**Path:** `GET /vocab/weak-words?limit=50`  
**Auth Required:** Yes  
**Query Params:**
- `limit: int = 50`
- `severity: Optional[str]` (GOOD | OK | BAD)

**Response:** `ApiResponse[list[WeakWordOut]]`
- `lexeme_id: UUID`
- `lemma: str`
- `type: LexemeType`
- `severity: Severity`
- `error_type: WordErrorType` (PRONUNCIATION | STRESS | INTONATION | MEANING | SPELLING | GRAMMAR | COLLOCATION | OTHER)
- `occur_count: int`
- `last_occurred_at: datetime`
- `evidence: Optional[Dict]`

---

## Module 5: LESSON ENGINE

### Sub-Resources: Lesson Items, Attempts, Scoring

#### 1. Create Lesson Item (MCQ, CLOZE, MATCH, REORDER, LISTEN, SPEAK)
**Path:** `POST /lesson-engine/items`  
**Auth Required:** Yes (permission: `LESSONITEM_CREATE`)  
**Request Schema:** `LessonItemCreate`
- `lesson_id: UUID` (required)
- `item_type: LessonItemType` (MCQ | CLOZE | MATCH | REORDER | LISTEN | SPEAK, required)
- `prompt: Optional[str]`
- `content: Optional[Dict]`
- `correct_answer: Optional[Dict]`
- `points: int = 1`
- `sort_order: int = 0`
- `choices: Optional[List[ChoiceCreate]]` (for MCQ/LISTEN)
  - `key: str`
  - `text: str`
  - `is_correct: bool = False`
  - `sort_order: int = 0`

**Response:** `ApiResponse[LessonItemOut]`

#### 2. Update Lesson Item
**Path:** `PATCH /lesson-engine/items/{item_id}`  
**Auth Required:** Yes (permission: `LESSONITEM_UPDATE`)  
**Request Schema:** `LessonItemUpdate`
- All fields optional

**Response:** `ApiResponse[LessonItemOut]`

#### 3. List Items by Lesson
**Path:** `GET /lesson-engine/items/by-lesson/{lesson_id}`  
**Auth Required:** Yes (permission: `LESSON_READ`)  
**Response:** `ApiResponse[list[LessonItemOut]]`

#### 4. Start Lesson Attempt
**Path:** `POST /lesson-engine/lessons/{lesson_id}/attempts/start`  
**Auth Required:** Yes (permission: `LESSON_ATTEMPT_START`)  
**Response:** `ApiResponse[AttemptStartResponse]`
- `attempt_id: UUID`
- `lesson_id: UUID`
- `items: List[LessonItemOut]` (choices have `is_correct=False` for security)

#### 5. Submit Lesson Attempt
**Path:** `POST /lesson-engine/attempts/{attempt_id}/submit`  
**Auth Required:** Yes (permission: `LESSON_ATTEMPT_SUBMIT`)  
**Request Schema:** `AttemptSubmitRequest`
- `answers: Dict[str, AnswerPayload]` - `{item_id: {answer, meta}}`
- `duration_sec: int = 0`

**Response:** `ApiResponse[AttemptSubmitResponse]`
- `attempt_id: UUID`
- `status: AttemptStatus` (STARTED | SUBMITTED | PENDING_AI | SCORED | FAILED)
- `score_points: int`
- `max_points: int`
- `score_percent: int`
- `results: List[ItemResult]`
  - `item_id: UUID`
  - `is_correct: bool`
  - `earned_points: int`
  - `max_points: int`
  - `detail: Optional[Dict]`

#### 6. Get Attempt
**Path:** `GET /lesson-engine/attempts/{attempt_id}`  
**Auth Required:** Yes  
**Response:** `ApiResponse[AttemptOut]`
- `id: UUID`
- `user_id: UUID`
- `lesson_id: UUID`
- `status: AttemptStatus`
- `started_at: datetime`
- `submitted_at: Optional[datetime]`
- `score_points: int`
- `max_points: int`
- `score_percent: int`
- `duration_sec: int`
- `answers: Optional[Dict]`
- `result_breakdown: Optional[Dict]`

#### 7. List User's Attempts
**Path:** `GET /lesson-engine/attempts/user/{user_id}?lesson_id={id}`  
**Auth Required:** Yes  
**Query Params:**
- `lesson_id: Optional[str]`
- `limit: int = 50`
- `offset: int = 0`

**Response:** `ApiResponse[AttemptsListResponse]`
- `items: List[AttemptOut]`
- `total: int`

#### 8. Update Attempt with AI Scoring (for SPEAK items)
**Path:** `POST /lesson-engine/attempts/{attempt_id}/ai-update`  
**Auth Required:** Yes (Admin/AI Worker)  
**Request Schema:** `AttemptAIUpdateRequest`
- `speak_results: Dict[str, SpeakItemAIResult]` - `{item_id: {pronunciation, fluency, accuracy, words}}`
- `finalize: bool = True`

**Response:** `ApiResponse[AttemptAIUpdateResponse]`
- `attempt_id: UUID`
- `status: AttemptStatus`
- `score_points: int`
- `max_points: int`
- `score_percent: int`

---

## Module 6: GRAMMAR ENGINE

### Sub-Resources: Topics, Patterns, Examples, Exercises, SRS

#### 1. Create Grammar Topic
**Path:** `POST /grammar/topics`  
**Auth Required:** Yes (permission: `GRAMMAR_TOPIC_CREATE`)  
**Request Schema:** `GrammarTopicCreate`
- `language_id: UUID` (required)
- `title: str` (min_length=1, max_length=180, required)
- `slug: str` (min_length=1, max_length=180, required)
- `description: Optional[str]`
- `sort_order: int = 0`
- `status: GrammarStatus = PUBLISHED` (DRAFT | PUBLISHED | ARCHIVED)

**Response:** `ApiResponse[GrammarTopicOut]`

#### 2. Update Grammar Topic
**Path:** `PATCH /grammar/topics/{topic_id}`  
**Auth Required:** Yes (permission: `GRAMMAR_TOPIC_UPDATE`)  
**Request Schema:** `GrammarTopicUpdate`

**Response:** `ApiResponse[GrammarTopicOut]`

#### 3. Get Grammar Topic
**Path:** `GET /grammar/topics/{topic_id}`  
**Auth Required:** Yes (permission: `GRAMMAR_TOPIC_READ`)  
**Response:** `ApiResponse[GrammarTopicOut]`

#### 4. List Grammar Topics
**Path:** `GET /grammar/topics?language_id={id}&status={status}&limit=50&offset=0`  
**Auth Required:** Yes (permission: `GRAMMAR_TOPIC_READ`)  
**Query Params:**
- `language_id: str` (required)
- `status: Optional[str]`
- `limit: int = 50`
- `offset: int = 0`

**Response:** `ApiResponse[list[GrammarTopicOut]]`

#### 5. Create Grammar Pattern
**Path:** `POST /grammar/patterns`  
**Auth Required:** Yes (permission: `GRAMMAR_PATTERN_CREATE`)  
**Request Schema:** `GrammarPatternCreate`
- `language_id: UUID` (required)
- `topic_id: Optional[UUID]`
- `title: str` (min_length=1, max_length=220, required)
- `short_rule: Optional[str]`
- `full_explanation: Optional[str]`
- `formula: Optional[Dict]`
- `common_mistakes: Optional[Dict]`
- `tags: Optional[Dict]`
- `difficulty: GrammarDifficulty = EASY` (EASY | MEDIUM | HARD)
- `status: GrammarStatus = PUBLISHED`

**Response:** `ApiResponse[GrammarPatternOut]`
- `id: UUID`
- `language_id: UUID`
- `topic_id: Optional[UUID]`
- `title: str`
- `short_rule: Optional[str]`
- `full_explanation: Optional[str]`
- `formula: Optional[Dict]`
- `common_mistakes: Optional[Dict]`
- `tags: Optional[Dict]`
- `difficulty: GrammarDifficulty`
- `status: GrammarStatus`
- `created_at: datetime`
- `updated_at: datetime`

#### 6. Update Grammar Pattern
**Path:** `PATCH /grammar/patterns/{pattern_id}`  
**Auth Required:** Yes (permission: `GRAMMAR_PATTERN_UPDATE`)  
**Request Schema:** `GrammarPatternUpdate`

**Response:** `ApiResponse[GrammarPatternOut]`

#### 7. Get Grammar Pattern
**Path:** `GET /grammar/patterns/{pattern_id}`  
**Auth Required:** Yes (permission: `GRAMMAR_PATTERN_READ`)  
**Response:** `ApiResponse[GrammarPatternOut]`

#### 8. List Grammar Patterns
**Path:** `GET /grammar/patterns?language_id={id}&topic_id={id}&q={query}&status={status}&limit=50&offset=0`  
**Auth Required:** Yes (permission: `GRAMMAR_PATTERN_READ`)  
**Query Params:**
- `language_id: str` (required)
- `topic_id: Optional[str]`
- `q: Optional[str]`
- `status: Optional[str]`
- `limit: int = 50`
- `offset: int = 0`

**Response:** `ApiResponse[list[GrammarPatternOut]]`

#### 9. Create Grammar Example
**Path:** `POST /grammar/examples`  
**Auth Required:** Yes (permission: `GRAMMAR_EXAMPLE_CREATE`)  
**Request Schema:** `GrammarExampleCreate`
- `pattern_id: UUID` (required)
- `sentence: str` (min_length=1, required)
- `translation: Optional[Dict]`
- `audio_url: Optional[str]`
- `highlight: Optional[Dict]`

**Response:** `ApiResponse[GrammarExampleOut]`

#### 10. Update Grammar Example
**Path:** `PATCH /grammar/examples/{example_id}`  
**Auth Required:** Yes (permission: `GRAMMAR_EXAMPLE_UPDATE`)  
**Request Schema:** `GrammarExampleUpdate`

**Response:** `ApiResponse[GrammarExampleOut]`

#### 11. Create Grammar Exercise
**Path:** `POST /grammar/exercises`  
**Auth Required:** Yes (permission: `GRAMMAR_EXERCISE_CREATE`)  
**Request Schema:** `GrammarExerciseCreate`
- `pattern_id: UUID` (required)
- `exercise_type: GrammarExerciseType` (MCQ | FILL_BLANK | REORDER | ERROR_CORRECTION | TRANSFORM)
- `prompt: str` (min_length=1, required)
- `data: Optional[Dict]`
- `answer: Optional[Dict]`
- `explanation: Optional[str]`
- `difficulty: GrammarDifficulty = EASY`

**Response:** `ApiResponse[GrammarExerciseOut]`

#### 12. Update Grammar Exercise
**Path:** `PATCH /grammar/exercises/{exercise_id}`  
**Auth Required:** Yes (permission: `GRAMMAR_EXERCISE_UPDATE`)  
**Request Schema:** `GrammarExerciseUpdate`

**Response:** `ApiResponse[GrammarExerciseOut]`

#### 13. Create Grammar Choice (for exercises)
**Path:** `POST /grammar/choices`  
**Auth Required:** Yes (permission: `GRAMMAR_CHOICE_CREATE`)  
**Request Schema:** `GrammarChoiceCreate`
- `exercise_id: UUID` (required)
- `text: str` (min_length=1, required)
- `is_correct: bool = False`
- `sort_order: int = 0`

**Response:** `ApiResponse[GrammarChoiceOut]`

#### 14. Attach Grammar to Lesson
**Path:** `POST /grammar/lessons/attach`  
**Auth Required:** Yes (permission: `GRAMMAR_LESSON_ATTACH`)  
**Request Schema:** `AttachGrammarToLessonRequest`
- `lesson_id: UUID` (required)
- `patterns: List[Dict]` - `[{pattern_id, is_core, sort_order}]`

**Response:** `ApiResponse[list[LessonGrammarOut]]`

#### 15. Get Grammar Session for SRS
**Path:** `GET /grammar/session?language_id={id}&limit=10`  
**Auth Required:** Yes  
**Query Params:**
- `language_id: str` (required)
- `limit: int = 10`

**Response:** `ApiResponse[list[GrammarSessionItem]]`
- `pattern: GrammarPatternOut`
- `examples: List[GrammarExampleOut]`
- `exercise: Optional[GrammarExerciseOut]`
- `choices: List[GrammarChoiceOut]`
- `state: Dict` (SRS state)

#### 16. Submit Grammar Session Result
**Path:** `POST /grammar/session/submit`  
**Auth Required:** Yes  
**Request Schema:** `GrammarSubmitRequest`
- `pattern_id: UUID` (required)
- `exercise_id: UUID` (required)
- `choice_id: UUID` (required) - user's selected answer
- `is_correct: bool` (server-computed)

**Response:** `ApiResponse[GrammarSubmitResponse]`
- `pattern_id: UUID`
- `is_correct: bool`
- `explanation: Optional[str]`
- `new_mastery: GrammarMastery` (NEW | LEARNING | KNOWN | MASTERED)

---

## Module 7: SPEAKING ENGINE

### Sub-Resources: Tasks, Attempts, Scoring

#### 1. Create Speaking Task (for admin/teacher)
**Path:** `POST /speaking/tasks`  
**Auth Required:** Yes (permission: `SPEAKING_TASK_CREATE`)  
**Request Schema:** `SpeakingTaskCreate`
- `language_id: UUID` (required)
- `task_type: SpeakingTaskType` (READ_ALOUD | REPEAT | QNA | PICTURE_DESC, required)
- `title: str` (min_length=1, max_length=200, required)
- `prompt_text: Optional[str]`
- `prompt_audio_url: Optional[str]`
- `reference_text: Optional[str]`
- `picture_url: Optional[str]`
- `difficulty: int` (default=1, 1-10)
- `tags: Optional[Dict]`
- `status: str = "PUBLISHED"`

**Response:** `ApiResponse[SpeakingTaskOut]`
- `id: UUID`
- `language_id: UUID`
- `task_type: SpeakingTaskType`
- `title: str`
- `prompt_text: Optional[str]`
- `prompt_audio_url: Optional[str]`
- `reference_text: Optional[str]`
- `picture_url: Optional[str]`
- `difficulty: int`
- `tags: Optional[Dict]`
- `status: str`
- `created_at: datetime`

#### 2. Update Speaking Task
**Path:** `PATCH /speaking/tasks/{task_id}`  
**Auth Required:** Yes (permission: `SPEAKING_TASK_UPDATE`)  
**Request Schema:** `SpeakingTaskUpdate`

**Response:** `ApiResponse[SpeakingTaskOut]`

#### 3. Get Speaking Task
**Path:** `GET /speaking/tasks/{task_id}`  
**Auth Required:** Yes  
**Response:** `ApiResponse[SpeakingTaskOut]`

#### 4. List Speaking Tasks
**Path:** `GET /speaking/tasks?language_id={id}&limit=50&offset=0`  
**Query Params:**
- `language_id: str` (required)
- `limit: int = 50`
- `offset: int = 0`

**Response:** `ApiResponse[list[SpeakingTaskOut]]`

#### 5. Start Speaking Attempt
**Path:** `POST /speaking/attempts/start`  
**Auth Required:** Yes  
**Request Schema:** `StartSpeakingAttemptRequest`
- `language_id: UUID` (required)
- `task_id: UUID` (required)

**Response:** `ApiResponse[StartSpeakingAttemptResponse]`
- `attempt_id: UUID`
- `task_id: UUID`
- `status: SpeakingAttemptStatus` (STARTED | SUBMITTED | PENDING_AI | SCORED | FAILED)
- `items: List[SpeakingAttemptItemOut]`
  - `id: UUID`
  - `prompt_text: Optional[str]`
  - `prompt_audio_url: Optional[str]`
  - `reference_text: Optional[str]`
  - `picture_url: Optional[str]`

#### 6. Submit Speaking Attempt
**Path:** `POST /speaking/attempts/{attempt_id}/submit`  
**Auth Required:** Yes  
**Request Schema:** `SubmitSpeakingAttemptRequest`
- `duration_sec: int = 0`
- `items: List[SubmitSpeakingAttemptItem]` (required)
  - `item_id: UUID`
  - `audio_url: Optional[str]`
  - `media_id: Optional[str]`
  - `audio_mime: str = "audio/wav"`
  - `duration_ms: int = 0`
- `strictness: int` (default=75, 0-100) - ELSA-like strictness

**Response:** `ApiResponse[SpeakingAttemptOut]`
- `id: UUID`
- `user_id: UUID`
- `language_id: UUID`
- `task_id: UUID`
- `status: SpeakingAttemptStatus`
- `duration_sec: int`
- `submitted_at: Optional[datetime]`
- `score_percent: int`
- `ai_result: Optional[Dict]`
- `created_at: datetime`
- `updated_at: datetime`

#### 7. Get Speaking Attempt
**Path:** `GET /speaking/attempts/{attempt_id}`  
**Auth Required:** Yes  
**Response:** `ApiResponse[SpeakingAttemptOut]`

#### 8. List User's Speaking Attempts
**Path:** `GET /speaking/attempts/user/{user_id}?task_id={id}`  
**Auth Required:** Yes  
**Query Params:**
- `task_id: Optional[str]`
- `limit: int = 50`
- `offset: int = 0`

**Response:** `ApiResponse[list[SpeakingAttemptOut]]`

#### 9. AI Score Speaking Attempt (webhook from AI service)
**Path:** `POST /speaking/attempts/{attempt_id}/ai-score`  
**Auth Required:** Yes (AI Worker)  
**Request Schema:** `SpeakingScorePayload`
- `score_percent: int` (0-100)
- `ai_result: Dict` (pronunciation, fluency, accuracy, etc.)
- `error: Optional[Dict]`

**Response:** `ApiResponse[SpeakingScoreOut]`
- `attempt_id: UUID`
- `status: SpeakingAttemptStatus`
- `score_percent: int`
- `ai_result: Optional[Dict]`
- `error: Optional[Dict]`

---

## Module 8: REVIEW (SRS - Spaced Repetition System)

### Sub-Resources: Review Sessions, Progress Tracking

#### 1. Get Today's Review Session
**Path:** `GET /review/today?language_id={id}&limit=20`  
**Auth Required:** Yes  
**Query Params:**
- `language_id: str` (required)
- `limit: int = 20` - items to review today

**Response:** `ApiResponse[ReviewTodayResponse]`
- `items: List[ReviewCard]`
  - Vocabulary cards + Grammar cards + Speaking tasks
- `total: int`

#### 2. Submit Review Result
**Path:** `POST /review/result`  
**Auth Required:** Yes  
**Request Schema:** `ReviewResultRequest`
- `item_type: str` (VOCAB | GRAMMAR | SPEAKING)
- `item_id: UUID` (lexeme_id | pattern_id | task_id)
- `rating: int` (0-5)
- `source: str` (SPEAKING | LISTENING | READING | WRITING | QUIZ)

**Response:** `ApiResponse[dict]`
- SRS state update (next_review_at, mastery_level, etc.)

#### 3. Get Review Stats
**Path:** `GET /review/stats?language_id={id}`  
**Auth Required:** Yes  
**Query Params:**
- `language_id: str` (required)

**Response:** `ApiResponse[dict]`
- `vocab_total: int`
- `vocab_mastered: int`
- `grammar_total: int`
- `grammar_mastered: int`
- `streak: int`
- `last_review: Optional[datetime]`

---

## Module 9: MEDIA (Google Drive Integration)

### Sub-Resources: File Upload, Download

#### 1. Upload File to Google Drive
**Path:** `POST /media/upload`  
**Auth Required:** Yes  
**Request:** Multipart form-data
- `file: File` (required)
- `folder_name: str` (optional) - GDrive folder to upload to

**Response:** `ApiResponse[dict]`
- `file_id: str` (Google Drive file ID)
- `file_name: str`
- `file_url: str` (shareable link)
- `mime_type: str`

#### 2. Get File Info
**Path:** `GET /media/files/{file_id}`  
**Auth Required:** Yes  
**Response:** `ApiResponse[dict]`
- `file_id: str`
- `file_name: str`
- `file_url: str`
- `mime_type: str`
- `size: int`

---

## Module 10: AI (Gemini Integration)

### Sub-Resources: Scoring, ASR, Monitoring

#### 1. Request AI Scoring (async)
**Path:** `POST /ai/score`  
**Auth Required:** Yes (Internal/Worker)  
**Request Schema:**
- `attempt_id: UUID` (SPEAK attempt)
- `audio_urls: List[str]`
- `reference_text: Optional[str]`
- `language: str`
- `task_type: SpeakingTaskType`

**Response:** `ApiResponse[dict]`
- `job_id: str` (async job ID for polling)
- `status: str` (QUEUED | PROCESSING | COMPLETED | FAILED)

#### 2. Poll Scoring Result
**Path:** `GET /ai/score/{job_id}`  
**Auth Required:** Yes  
**Response:** `ApiResponse[dict]`
- `status: str`
- `result: Optional[Dict]` (pronunciation, fluency, accuracy, etc.)
- `error: Optional[str]`

#### 3. AI Health Check
**Path:** `GET /ai/health`  
**Response:** `ApiResponse[dict]`
- `status: str` (OK | ERROR)
- `queue_size: int`
- `workers_active: int`

---

## Database Models Summary

### Core Models
- `User` - user profile
- `UserIdentity` - email/phone identities
- `AuthSession` - session tokens
- `TrustedDevice` - biometric trusted devices
- `PasswordReset` - password reset tokens

### Curriculum Models
- `Language` - languages (English, Vietnamese, etc.)
- `Level` - proficiency levels (A1, A2, B1, etc.)
- `Unit` - course units
- `Lesson` - lessons with content

### Vocabulary Models
- `Lexeme` - word entries
- `Sense` - word definitions/meanings
- `Example` - example sentences
- `LessonLexeme` - lesson-vocabulary mapping
- `UserWordMastery` - SRS state for vocabulary

### Lesson Models
- `LessonItem` - quiz items (MCQ, CLOZE, SPEAK, etc.)
- `Choice` - multiple choice options
- `LessonAttempt` - user attempt at lesson
- `AttemptAnswer` - answers per item

### Grammar Models
- `GrammarTopic` - grammar topics
- `GrammarPattern` - grammar rules/patterns
- `GrammarExample` - example sentences
- `GrammarExercise` - practice exercises
- `GrammarChoice` - multiple choice for exercises
- `UserGrammarMastery` - SRS state for grammar

### Speaking Models
- `SpeakingTask` - speaking practice tasks
- `SpeakingAttempt` - user speaking attempt
- `SpeakingItem` - task items (prompts, reference)

### RBAC Models
- `Role` - user roles (admin, teacher, student, etc.)
- `Permission` - granular permissions (ROLE_MANAGE, USER_MANAGE, etc.)
- `UserRole` - user-role mapping
- `RolePermission` - role-permission mapping

---

## Enums Summary

| Category | Values |
|----------|--------|
| **IdentityType** | EMAIL, PHONE |
| **IdentityStatus** | PENDING_VERIFY, VERIFIED, DISABLED |
| **UserStatus** | ACTIVE, SUSPENDED, DELETED |
| **SessionStatus** | ACTIVE, REVOKED, EXPIRED |
| **OtpPurpose** | LOGIN_2FA, VERIFY_PHONE, RESET_PASSWORD |
| **OtpStatus** | CREATED, SENT, VERIFIED, EXPIRED, FAILED, LOCKED |
| **OtpChannel** | SMS, EMAIL |
| **ResetStatus** | PENDING, USED, EXPIRED, REVOKED |
| **LessonType** | STANDARD, BOSS, REVIEW |
| **LessonItemType** | MCQ, CLOZE, MATCH, REORDER, LISTEN, SPEAK |
| **AttemptStatus** | STARTED, SUBMITTED, PENDING_AI, SCORED, FAILED |
| **PublishStatus** | DRAFT, REVIEW, PUBLISHED, ARCHIVED |
| **LexemeType** | NOUN, VERB, ADJ, ADV, PREP, PHRASE, OTHER |
| **WordDomain** | DAILY, ACADEMIC, BUSINESS, TRAVEL, TECH, OTHER |
| **WordMastery** | NEW, LEARNING, KNOWN, MASTERED |
| **WordErrorType** | PRONUNCIATION, STRESS, INTONATION, MEANING, SPELLING, GRAMMAR, COLLOCATION, OTHER |
| **Severity** | GOOD, OK, BAD |
| **GrammarStatus** | DRAFT, PUBLISHED, ARCHIVED |
| **GrammarDifficulty** | EASY, MEDIUM, HARD |
| **GrammarExerciseType** | MCQ, FILL_BLANK, REORDER, ERROR_CORRECTION, TRANSFORM |
| **GrammarMastery** | NEW, LEARNING, KNOWN, MASTERED |
| **SpeakingTaskType** | READ_ALOUD, REPEAT, QNA, PICTURE_DESC |
| **SpeakingAttemptStatus** | STARTED, SUBMITTED, PENDING_AI, SCORED, FAILED |
| **EntityStatus** | ACTIVE, DISABLED |

---

## Authentication & Authorization

### JWT Structure
```
Header: { alg: "HS256", typ: "JWT" }
Payload: { 
  user_id: UUID,
  exp: timestamp,
  iat: timestamp 
}
```

### Default Permissions (per module)
- **AUTH**: No permission required (public endpoints)
- **RBAC**: `ROLE_MANAGE`, `USER_MANAGE`
- **CURRICULUM**: `LESSON_CREATE`, `LESSON_UPDATE`, `LESSON_READ`, `LESSON_DELETE`
- **VOCABULARY**: `VOCAB_LEXEME_*`, `VOCAB_SENSE_*`, `VOCAB_EXAMPLE_*`, `VOCAB_LESSON_ATTACH`
- **LESSON_ENGINE**: `LESSONITEM_CREATE`, `LESSONITEM_UPDATE`, `LESSON_ATTEMPT_START`, `LESSON_ATTEMPT_SUBMIT`, `LESSON_READ`
- **GRAMMAR_ENGINE**: `GRAMMAR_TOPIC_*`, `GRAMMAR_PATTERN_*`, `GRAMMAR_EXERCISE_*`, `GRAMMAR_CHOICE_*`, `GRAMMAR_LESSON_ATTACH`
- **SPEAKING_ENGINE**: `SPEAKING_TASK_CREATE`, `SPEAKING_TASK_UPDATE`, `SPEAKING_TASK_DELETE`
- **REVIEW**: No special permission required
- **MEDIA**: `MEDIA_UPLOAD`, `MEDIA_DELETE`

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Refresh token TTL |
| `OTP_EXPIRE_MINUTES` | 5 | OTP code validity |
| `OTP_MAX_ATTEMPTS` | 5 | Max OTP verify attempts |
| `OTP_DEBUG_LOG` | true | Log OTP codes in console |
| `REDIS_URL` | redis://localhost:6379/0 | Redis cache URL |
| `RBAC_CACHE_TTL_SECONDS` | 120 | RBAC permission cache TTL |
| `TRUSTED_DEVICE_TTL_DAYS` | 30 | Trusted device validity |
| `PASSWORD_RESET_TTL_MINUTES` | 60 | Password reset token TTL |
| `AUTO_BOOTSTRAP` | true | Auto-seed RBAC on startup |
| `GEMINI_API_KEY` | - | Gemini AI API key |
| `GDRIVE_FOLDER_ID` | - | Google Drive folder for uploads |
| `AI_RATE_GLOBAL_PER_MIN` | 120 | Max AI requests/minute |
| `AI_RATE_USER_PER_MIN` | 10 | Max AI requests per user/minute |

---

**Last Updated:** February 1, 2026  
**Current Branch:** development  
**Repository:** nhattai8888/API_Learning_Language

