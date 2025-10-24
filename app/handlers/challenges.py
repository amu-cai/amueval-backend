from fastapi import (
    HTTPException,
    UploadFile,
)
from pathlib import Path
from pydantic import (
    BaseModel,
    Field,
    validator,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from database.challenges import (
    add_challenge,
    all_challenges,
    check_challenge_author,
    check_challenge_exists,
    edit_challenge,
    get_challenge,
)
from database.evaluations import (
    test_best_score,
)
from database.submissions import (
    challenge_participants_ids,
)
from database.tests import (
    add_tests,
    challenge_additional_metrics,
    challenge_main_metric,
)
from database.users import (
    challenge_participants_names,
    check_user_exists,
    check_user_is_admin,
)
from handlers.files import save_expected_file
from metrics.metrics import Metrics


URLS_WHITELIST = [
    "https://git.wmi.amu.edu.pl",
    "https://github.com",
    "https://gitlab.com",
    "https://codeberg.org",
    "https://bitbucket.org",
    "https://sourceforge.net",
    "https://www.kaggle.com",
    "https://kaggle.com/
]

FORBIDDEN_WORDS = [
    "chuj", "chuja", "chujek", "chuju", "chujem", "chujnia", "chujowy",
    "chujowa", "chujowe", "cipa", "cipę", "cipe", "cipą", "cipie", "dojebać",
    "dojebac", "dojebie", "dojebał", "dojebal", "dojebała", "dojebala",
    "dojebałem", "dojebalem", "dojebałam", "dojebalam", "dojebię", "dojebie",
    "dopieprzać", "dopieprzac", "dopierdalać", "dopierdalac", "dopierdala",
    "dopierdalał", "dopierdalal", "dopierdalała", "dopierdalala", "dopierdoli",
    "dopierdolił", "dopierdolil", "dopierdolę", "dopierdole", "dopierdoli",
    "dopierdalający", "dopierdalajacy", "dopierdolić", "dopierdolic", "dupa",
    "dupie", "dupą", "dupcia", "dupeczka", "dupy", "dupe", "huj", "hujek",
    "hujnia", "huja", "huje", "hujem", "huju", "jebać", "jebac", "jebał",
    "jebal", "jebie", "jebią", "jebia", "jebak", "jebaka", "jebal", "jebał",
    "jebany", "jebane", "jebanka", "jebanko", "jebankiem", "jebanymi",
    "jebana", "jebanym", "jebanej", "jebaną", "jebana", "jebani", "jebanych",
    "jebanymi", "jebcie", "jebiący", "jebiacy", "jebiąca", "jebiaca",
    "jebiącego", "jebiacego", "jebiącej", "jebiacej", "jebia", "jebią",
    "jebie", "jebię", "jebliwy", "jebnąć", "jebnac", "jebnąc", "jebnać",
    "jebnął", "jebnal", "jebną", "jebna", "jebnęła", "jebnela", "jebnie",
    "jebnij", "jebut", "koorwa", "kórwa", "kurestwo", "kurew", "kurewski",
    "kurewska", "kurewskiej", "kurewską", "kurewska", "kurewsko", "kurewstwo",
    "kurwa", "kurwaa", "kurwami", "kurwą", "kurwe", "kurwę", "kurwie",
    "kurwiska", "kurwo", "kurwy", "kurwach", "kurwami", "kurewski", "kurwiarz",
    "kurwiący", "kurwica", "kurwić", "kurwic", "kurwidołek", "kurwik",
    "kurwiki", "kurwiszcze", "kurwiszon", "kurwiszona", "kurwiszonem",
    "kurwiszony", "kutas", "kutasa", "kutasie", "kutasem", "kutasy", "kutasów",
    "kutasow", "kutasach", "kutasami", "matkojebca", "matkojebcy",
    "matkojebcą", "matkojebca", "matkojebcami", "matkojebcach", "nabarłożyć",
    "najebać", "najebac", "najebał", "najebal", "najebała", "najebala",
    "najebane", "najebany", "najebaną", "najebana", "najebie", "najebią",
    "najebia", "naopierdalać", "naopierdalac", "naopierdalał", "naopierdalal",
    "naopierdalała", "naopierdalala", "naopierdalała", "napierdalać",
    "napierdalac", "napierdalający", "napierdalajacy", "napierdolić",
    "napierdolic", "nawpierdalać", "nawpierdalac", "nawpierdalał",
    "nawpierdalal", "nawpierdalała", "nawpierdalala", "obsrywać", "obsrywac",
    "obsrywający", "obsrywajacy", "odpieprzać", "odpieprzac", "odpieprzy",
    "odpieprzył", "odpieprzyl", "odpieprzyła", "odpieprzyla", "odpierdalać",
    "odpierdalac", "odpierdol", "odpierdolił", "odpierdolil", "odpierdoliła",
    "odpierdolila", "odpierdoli", "odpierdalający", "odpierdalajacy",
    "odpierdalająca", "odpierdalajaca", "odpierdolić", "odpierdolic",
    "odpierdoli", "odpierdolił", "opieprzający", "opierdalać", "opierdalac",
    "opierdala", "opierdalający", "opierdalajacy", "opierdol", "opierdolić",
    "opierdolic", "opierdoli", "opierdolą", "opierdola", "piczka",
    "pieprznięty", "pieprzniety", "pieprzony", "pierdel", "pierdlu",
    "pierdolą", "pierdola", "pierdolący", "pierdolacy", "pierdoląca",
    "pierdolaca", "pierdol", "pierdole", "pierdolenie", "pierdoleniem",
    "pierdoleniu", "pierdolę", "pierdolec", "pierdola", "pierdolą",
    "pierdolić", "pierdolicie", "pierdolic", "pierdolił", "pierdolil",
    "pierdoliła", "pierdolila", "pierdoli", "pierdolnięty", "pierdolniety",
    "pierdolisz", "pierdolnąć", "pierdolnac", "pierdolnął", "pierdolnal",
    "pierdolnęła", "pierdolnela", "pierdolnie", "pierdolnięty", "pierdolnij",
    "pierdolnik", "pierdolona", "pierdolone", "pierdolony", "pierdołki",
    "pierdzący", "pierdzieć", "pierdziec", "pizda", "pizdą", "pizde", "pizdę",
    "piździe", "pizdzie", "pizdnąć", "pizdnac", "pizdu", "podpierdalać",
    "podpierdalac", "podpierdala", "podpierdalający", "podpierdalajacy",
    "podpierdolić", "podpierdolic", "podpierdoli", "pojeb", "pojeba",
    "pojebami", "pojebani", "pojebanego", "pojebanemu", "pojebani", "pojebany",
    "pojebanych", "pojebanym", "pojebanymi", "pojebem", "pojebać", "pojebac",
    "pojebalo", "popierdala", "popierdalac", "popierdalać", "popierdolić",
    "popierdolic", "popierdoli", "popierdolonego", "popierdolonemu",
    "popierdolonym", "popierdolone", "popierdoleni", "popierdolony",
    "porozpierdalać", "porozpierdala", "porozpierdalac", "poruchac",
    "poruchać", "przejebać", "przejebane", "przejebac", "przyjebali",
    "przepierdalać", "przepierdalac", "przepierdala", "przepierdalający",
    "przepierdalajacy", "przepierdalająca", "przepierdalajaca",
    "przepierdolić", "przepierdolic", "przyjebać", "przyjebac", "przyjebie",
    "przyjebała", "przyjebala", "przyjebał", "przyjebal", "przypieprzać",
    "przypieprzac", "przypieprzający", "przypieprzajacy", "przypieprzająca",
    "przypieprzajaca", "przypierdalać", "przypierdalac", "przypierdala",
    "przypierdoli", "przypierdalający", "przypierdalajacy", "przypierdolić",
    "przypierdolic", "qrwa", "rozjebać", "rozjebac", "rozjebie", "rozjebała",
    "rozjebią", "rozpierdalać", "rozpierdalac", "rozpierdala", "rozpierdolić",
    "rozpierdolic", "rozpierdole", "rozpierdoli", "rozpierducha", "skurwić",
    "skurwiel", "skurwiela", "skurwielem", "skurwielu", "skurwysyn",
    "skurwysynów", "skurwysynow", "skurwysyna", "skurwysynem", "skurwysynu",
    "skurwysyny", "skurwysyński", "skurwysynski", "skurwysyństwo",
    "skurwysynstwo", "spieprzać", "spieprzac", "spieprza", "spieprzaj",
    "spieprzajcie", "spieprzają", "spieprzaja", "spieprzający", "spieprzajacy",
    "spieprzająca", "spieprzajaca", "spierdalać", "spierdalac", "spierdala",
    "spierdalał", "spierdalała", "spierdalal", "spierdalalcie", "spierdalala",
    "spierdalający", "spierdalajacy", "spierdolić", "spierdolic", "spierdoli",
    "spierdoliła", "spierdoliło", "spierdolą", "spierdola", "srać", "srac",
    "srający", "srajacy", "srając", "srajac", "sraj", "sukinsyn", "sukinsyny",
    "sukinsynom", "sukinsynowi", "sukinsynów", "sukinsynow", "śmierdziel",
    "udupić", "ujebać", "ujebac", "ujebał", "ujebal", "ujebana", "ujebany",
    "ujebie", "ujebała", "ujebala", "upierdalać", "upierdalac", "upierdala",
    "upierdoli", "upierdolić", "upierdolic", "upierdoli", "upierdolą",
    "upierdola", "upierdoleni", "wjebać", "wjebac", "wjebie", "wjebią",
    "wjebia", "wjebiemy", "wjebiecie", "wkurwiać", "wkurwiac", "wkurwi",
    "wkurwia", "wkurwiał", "wkurwial", "wkurwiający", "wkurwiajacy",
    "wkurwiająca", "wkurwiajaca", "wkurwić", "wkurwic", "wkurwi", "wkurwiacie",
    "wkurwiają", "wkurwiali", "wkurwią", "wkurwia", "wkurwimy", "wkurwicie",
    "wkurwiacie", "wkurwić", "wkurwic", "wkurwia", "wpierdalać", "wpierdalac",
    "wpierdalający", "wpierdalajacy", "wpierdol", "wpierdolić", "wpierdolic",
    "wpizdu", "wyjebać", "wyjebac", "wyjebali", "wyjebał", "wyjebac",
    "wyjebała", "wyjebały", "wyjebie", "wyjebią", "wyjebia", "wyjebiesz",
    "wyjebie", "wyjebiecie", "wyjebiemy", "wypieprzać", "wypieprzac",
    "wypieprza", "wypieprzał", "wypieprzal", "wypieprzała", "wypieprzala",
    "wypieprzy", "wypieprzyła", "wypieprzyla", "wypieprzył", "wypieprzyl",
    "wypierdal", "wypierdalać", "wypierdalac", "wypierdala", "wypierdalaj",
    "wypierdalał", "wypierdalal", "wypierdalała", "wypierdalala",
    "wypierdalać", "wypierdolić", "wypierdolic", "wypierdoli", "wypierdolimy",
    "wypierdolicie", "wypierdolą", "wypierdola", "wypierdolili", "wypierdolił",
    "wypierdolil", "wypierdoliła", "wypierdolila", "zajebać", "zajebac",
    "zajebie", "zajebią", "zajebia", "zajebiał", "zajebial", "zajebała",
    "zajebiala", "zajebali", "zajebana", "zajebani", "zajebane", "zajebany",
    "zajebanych", "zajebanym", "zajebanymi", "zajebiste", "zajebisty",
    "zajebistych", "zajebista", "zajebistym", "zajebistymi", "zajebiście",
    "zajebiscie", "zapieprzyć", "zapieprzyc", "zapieprzy", "zapieprzył",
    "zapieprzyl", "zapieprzyła", "zapieprzyla", "zapieprzą", "zapieprza",
    "zapieprzy", "zapieprzymy", "zapieprzycie", "zapieprzysz", "zapierdala",
    "zapierdalać", "zapierdalac", "zapierdalaja", "zapierdalał", "zapierdalaj",
    "zapierdalajcie", "zapierdalała", "zapierdalala", "zapierdalali",
    "zapierdalający", "zapierdalajacy", "zapierdolić", "zapierdolic",
    "zapierdoli", "zapierdolił", "zapierdolil", "zapierdoliła", "zapierdolila",
    "zapierdolą", "zapierdola", "zapierniczać", "zapierniczający", "zasrać",
    "zasranym", "zasrywać", "zasrywający", "zesrywać", "zesrywający", "zjebać",
    "zjebac", "zjebał", "zjebal", "zjebała", "zjebala", "zjebana", "zjebią",
    "zjebali", "zjeby", "anus", "ballsack", "bastard", "bitch",
    "biatch", "blowjob", "blow job", "bollock", "bollok", "boner",
    "boob", "bugger", "buttplug", "clitoris", "cock", "crap", "cunt", "damn", "dick", "dildo", "dyke", "feck", "fellate",
    "fellatio", "felching", "fuck", "f u c k", "fudgepacker", "fudge packer",
    "flange", "Goddamn", "God damn", "jerk", "knobend",
    "knob end", "labia", "lmao", "lmfao", "muff", "nigger", "nigga", "omg",
    "penis", "piss", "poop", "prick", "pussy", "queer", "scrotum", 
    "shit", "s hit", "sh1t", "smegma", "spunk", "tosser", "twat", "vagina", "whore", "wtf"
]


class CreateChallengeRerquest(BaseModel):
    author: str = Field(max_length=15)
    title: str = Field(max_length=50)
    source: str
    type: str
    description: str = Field(max_length=200)
    deadline: str
    award: str
    metric: str
    parameters: str
    sorting: str
    additional_metrics: str

    @validator("title")
    def title_does_not_contain_curses(cls, v):
        if any(word in v for word in FORBIDDEN_WORDS):
            raise ValueError("Title cannot contain curses")
        return v

    @validator("description")
    def description_does_not_contain_curses(cls, v):
        if any(word in v for word in FORBIDDEN_WORDS):
            raise ValueError("Description cannot contain curses")
        return v

    @validator("source")
    def source_from_whitelist(cls, v):
        if not any(v.startswith(url) for url in URLS_WHITELIST):
            raise ValueError(f"Source has to be from one of: {URLS_WHITELIST}")
        return v


class CreateChallengeResponse(BaseModel):
    message: str = "Challenge created"
    challenge_title: str
    main_metric: str


class EditChallengeRequest(BaseModel):
    user: str
    title: str = Field(max_length=30)
    description: str = Field(max_length=300)
    deadline: str

    @validator("title")
    def title_does_not_contain_curses(cls, v):
        if any(word in v for word in FORBIDDEN_WORDS):
            raise ValueError("Title cannot contain curses")
        return v

    @validator("description")
    def description_does_not_contain_curses(cls, v):
        if any(word in v for word in FORBIDDEN_WORDS):
            raise ValueError("Description cannot contain curses")
        return v


class GetChallengeResponse(BaseModel):
    id: int
    title: str
    type: str
    description: str
    main_metric: str
    best_sore: float | None
    deadline: str
    award: str
    deleted: bool
    sorting: str
    participants: int


class GetChallengesResponse(BaseModel):
    challenges: list[GetChallengeResponse]


class ChallengeInfoResponse(BaseModel):
    id: int
    title: str
    author: str
    type: str
    mainMetric: str
    mainMetricParameters: str
    description: str
    source: str
    bestScore: float | None
    deadline: str
    award: str
    deleted: bool
    sorting: str
    participants: int
    additional_metrics: list[str]


async def create_challenge_handler(
    async_session: async_sessionmaker[AsyncSession],
    request: CreateChallengeRerquest,
    file: UploadFile,
) -> CreateChallengeResponse:
    """
    Creates a challenge from given @CreateChallengeRerquest and a '.tsv' file.
    """
    # Checking user
    author_exists = await check_user_exists(
        async_session=async_session, user_name=request.author
    )
    if not author_exists:
        raise HTTPException(status_code=401, detail="User does not exist")

    # Checking title
    challenge_exists = await check_challenge_exists(
        async_session=async_session, title=request.title
    )
    if challenge_exists or request.title == "":
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title cannot be empty or challenge title <{
                request.title}> already exists",
        )

    # Checking file name
    proper_file_extension = ".tsv" == Path(file.filename).suffix
    if not proper_file_extension:
        raise HTTPException(
            status_code=415,
            detail=f"File <{file.filename}> is not a TSV file",
        )

    # Creating challenge
    added_challenge = await add_challenge(
        async_session=async_session,
        user_name=request.author,
        title=request.title,
        source=request.source,
        description=request.description,
        type=request.type,
        deadline=request.deadline,
        award=request.award,
    )

    # Creating tests for the challenge
    added_tests = await add_tests(
        async_session=async_session,
        challenge=added_challenge.get("challenge_id"),
        main_metric=request.metric,
        main_metric_parameters=request.parameters,
        additional_metrics=request.additional_metrics,
    )

    # Saving 'expected' file with name of the challenge
    await save_expected_file(file, request.title)

    # Testing, if the main metric works with the data
    # TODO: check if this can be done after modification to evaluation function

    return CreateChallengeResponse(
        challenge_title=added_challenge.get("challenge_title"),
        main_metric=added_tests.get("test_main_metric"),
    )


async def edit_challenge_handler(
    async_session: async_sessionmaker[AsyncSession],
    request: EditChallengeRequest,
) -> None:
    """
    Allows to edit deadline and description of a challenge.
    """
    print(request)
    if request.title == "":
        raise HTTPException(
            status_code=422, detail="Challenge title cannot be empty")

    challenge_exists = await check_challenge_exists(
        async_session=async_session, title=request.title
    )
    if not challenge_exists:
        raise HTTPException(
            status_code=422,
            detail=f"Challenge title <{request.title}> does not exist",
        )

    challenge_belongs_to_user = await check_challenge_author(
        async_session=async_session,
        challenge_title=request.title,
        user_name=request.user,
    )
    user_is_admin = await check_user_is_admin(
        async_session=async_session,
        user_name=request.user,
    )
    if (not challenge_belongs_to_user) and (not user_is_admin):
        raise HTTPException(
            status_code=403,
            detail=f"Challenge <{
                request.title}> does not belong to user <{request.user}> or user is not an admin",
        )

    await edit_challenge(
        async_session=async_session,
        title=request.title,
        description=request.description,
        deadline=request.deadline,
    )

    return None


async def get_challenges_handler(
    async_session: async_sessionmaker[AsyncSession],
) -> GetChallengesResponse:
    """
    Returns list of all challenges.
    """
    challenges = await all_challenges(async_session=async_session)

    results = []
    for challenge in challenges:
        main_test = await challenge_main_metric(
            async_session=async_session,
            challenge_id=challenge.id,
        )

        main_metric = getattr(Metrics(), main_test.metric)
        sorting = main_metric().sorting

        participants = await challenge_participants_ids(
            async_session=async_session, challenge_id=challenge.id
        )

        best_score = await test_best_score(
            async_session=async_session,
            test_id=main_test.id,
            sorting=sorting,
        )

        results.append(
            GetChallengeResponse(
                id=challenge.id,
                title=challenge.title,
                type=challenge.type,
                description=challenge.description,
                main_metric=main_test.metric,
                best_sore=best_score,
                deadline=challenge.deadline,
                award=challenge.award,
                deleted=challenge.deleted,
                sorting=sorting,
                participants=len(participants),
            )
        )

    return GetChallengesResponse(challenges=results)


async def challenge_info_handler(
    async_session: async_sessionmaker[AsyncSession],
    title: str,
):
    """
    Returns information about a given challenge.
    """
    challenge_exists = await check_challenge_exists(
        async_session=async_session, title=title
    )
    if not challenge_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Challenge <{title}> does not exist",
        )

    challenge = await get_challenge(
        async_session=async_session,
        title=title,
    )

    main_test = await challenge_main_metric(
        async_session=async_session,
        challenge_id=challenge.id,
    )
    main_metric = getattr(Metrics(), main_test.metric)
    sorting = main_metric().sorting

    additional_tests = await challenge_additional_metrics(
        async_session=async_session,
        challenge_id=challenge.id,
    )
    additional_metrics = [test.metric for test in additional_tests]

    participants = len(
        await challenge_participants_names(
            async_session=async_session,
            challenge_id=challenge.id,
        )
    )

    best_score = await test_best_score(
        async_session=async_session,
        test_id=main_test.id,
        sorting=sorting,
    )

    return ChallengeInfoResponse(
        id=challenge.id,
        title=challenge.title,
        author=challenge.author,
        type=challenge.type,
        mainMetric=main_test.metric,
        mainMetricParameters=main_test.metric_parameters,
        description=challenge.description,
        source=challenge.source,
        bestScore=best_score,
        deadline=challenge.deadline,
        award=challenge.award,
        deleted=challenge.deleted,
        sorting=sorting,
        participants=participants,
        additional_metrics=additional_metrics,
    )
