## ADDED Requirements

### Requirement: Публикация образа по тегу версии

Workflow SHALL запускаться при пуше git-тега, начинающегося с `v`, собирать образ из `Dockerfile` и публиковать его в Docker Hub. Публикуемый образ SHALL именоваться `<DOCKERHUB_USERNAME>/book-shelf`.

#### Scenario: Пуш тега запускает публикацию
- **WHEN** в репозиторий пушится тег `v1.2.3`
- **THEN** GitHub Actions запускает workflow, собирает образ и публикует его в Docker Hub

#### Scenario: Версии берутся из git-тега
- **WHEN** опубликован тег `v1.2.3`
- **THEN** в Docker Hub появляются теги образа `1.2.3`, `1.2` и `latest`

#### Scenario: Pre-release не обновляет latest
- **WHEN** пушится тег `v1.2.3-rc.1`
- **THEN** публикуются теги `1.2.3-rc.1` и `1.2`, но тег `latest` не перетирается

#### Scenario: Сокращённый тег vX.Y получает версионный тег
- **WHEN** пушится тег `v1.1`
- **THEN** публикуются теги образа `1.1` и `latest`

#### Scenario: Обычный пуш не запускает публикацию
- **WHEN** в ветку пушится коммит без тега `v*`
- **THEN** workflow публикации не запускается

### Requirement: Учётные данные Docker Hub через секреты

Workflow SHALL брать логин и токен Docker Hub из секретов репозитория `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`. Учётные данные MUST NOT храниться в файлах репозитория.

#### Scenario: Логин в Docker Hub перед пушем
- **WHEN** workflow выполняется
- **THEN** шаг логина использует `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN` из секретов, а в логах шага токен замаскирован
