from datetime import datetime, timezone

from pydantic import BaseModel

from src.settings import TIMEZONE, ScrapperSettings

scrapper_settings = ScrapperSettings()


class StackOverflowApiResponseOwner(BaseModel):
    display_name: str | None
    link: str | None


class StackOverflowApiResponse(BaseModel):
    question_id: int
    title: str | None
    body: str | None
    owner: StackOverflowApiResponseOwner
    link: str | None
    creation_date: int | None = None
    last_activity_date: int | None = None

    def model_post_init(self, __context) -> None:  # type: ignore  # noqa: ANN001
        if self.creation_date:
            self.creation_date = datetime.fromtimestamp(
                self.creation_date,
                tz=TIMEZONE,
            )  # type: ignore
        if self.last_activity_date:
            self.last_activity_date = datetime.fromtimestamp(
                self.last_activity_date,
                tz=TIMEZONE,
            )  # type: ignore
        if self.body:
            self.body = self.body[: scrapper_settings.body_max_len]

    def get_description(self) -> str:
        return f"""Обновление по ссылке: {self.link}
имя пользователя: {self.owner.display_name}
время создания: {self.last_activity_date}

`{self.title}`

`{self.body}`
"""


class GitHubApiResponseUser(BaseModel):
    login: str | None
    url: str | None


class GitHubApiResponse(BaseModel):
    title: str | None
    body: str | None
    user: GitHubApiResponseUser
    html_url: str | None
    created_at: None | datetime = None
    updated_at: None | datetime = None

    def model_post_init(self, __context) -> None:  # type: ignore  # noqa: ANN001
        if self.title:
            self.title = self.title[: scrapper_settings.title_max_len]
        if self.created_at:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc).astimezone(tz=TIMEZONE)
        if self.updated_at:
            self.updated_at = self.updated_at.replace(tzinfo=timezone.utc).astimezone(tz=TIMEZONE)
        if self.body:
            self.body = self.body[: scrapper_settings.body_max_len]

    def get_description(self) -> str:
        return f"""ссылка: {self.html_url}
имя пользователя: {self.user.login}
время создания: {self.created_at}
время обновления: {self.updated_at}

`{self.title}`

`{self.body}`
------------------------------------------
"""
