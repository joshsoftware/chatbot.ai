from src.embeddings.sentenceSegmentation import SentenceSegmentationService
from src.embeddings.createEmbeddings import process_sentences_and_store, get_embeddings_transformer
from sqlmodel import String

class EmbeddingService:
    def __init__(self):
        # Initialize the segmentation and embedding services
        self.segmentation_service = SentenceSegmentationService()

    async def process_file(self, file_path, session, org_id):
        """
        Process the given file, segment it into sentences, and store embeddings.
        
        :param file_path: Path to the file containing text to segment and process
        :param session: Database or session instance used for storing the embeddings
        :param org_meta: Organization metadata (e.g., {'id': 123})
        :return: bool - True for success, False for failure
        """
        try:
            # Segment the file content into sentences
            sentences = self.segmentation_service.segment_content(file_path)

            # Process the sentences and store embeddings in the database
            await process_sentences_and_store(sentences, org_id, session)
            
            # If processing is successful, return True
            return True
        except Exception as e:
            # If an error occurs, log and return False
            print(f"Error processing file: {str(e)}")
            return False

    async def get_query_vector(self, sentence: String) -> dict:
        embeddings = await get_embeddings_transformer([sentence])
        return embeddings[0]
