from src.embeddings.service import EmbeddingService
from db.index import UserSession
from db.schema import Orgnization


async def save_embeddings(data: Orgnization, session: UserSession) -> None:
    """
    Process the file to generate embeddings and associate them with the given organization metadata.
    
    :param data: A dictionary containing data like file path
    :param session: A session instance for interacting with the database
    :param org_meta: Organization metadata to associate with the embeddings
    :return: None
    """
    # Step: Call the EmbeddingService to process the file and generate embeddings
    embedding_service = EmbeddingService()
    print(data)
    await embedding_service.process_file(data.filePath, session, data.id)