from src.repository.link_repository import LinkRepositoryLocal
from src.repository.link_service import LinkService

link_repository = LinkRepositoryLocal()
link_service = LinkService(link_repository)
