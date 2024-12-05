import os
import torch
from transformers import AutoModel, AutoTokenizer
from sklearn.preprocessing import normalize
from sqlmodel import SQLModel, Field, Column, JSON, Integer, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ARRAY
from db.schema import OrgDataEmbedding
from db.index import UserSession
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VECTOR_DIM = int(os.getenv("VECTOR_DIM", 1024))

# Your model directory path
model_dir = os.getenv("EMBEDDING_MODEL_PATH")

# Initialize model and tokenizer
model = AutoModel.from_pretrained(model_dir, trust_remote_code=True).eval()

# Explicitly move model to CPU (this will work on Mac since CUDA is not supported)
model.to(torch.device("cpu"))

tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)

# Linear layer for transforming the embeddings to the desired vector dimension
vector_linear = torch.nn.Linear(in_features=model.config.hidden_size, out_features=VECTOR_DIM)
vector_linear.load_state_dict({
    k.replace("linear.", ""): v for k, v in
    torch.load(os.path.join(model_dir, f"2_Dense_{VECTOR_DIM}/pytorch_model.bin"), map_location=torch.device("cpu")).items()
})

# Function to get embeddings from transformer model
async def get_embeddings_transformer(sentences: list) -> list[list[float]]:
    """
    Generate embeddings for the given sentences using a transformer model.
    Args:
        sentences (list[str]): List of sentences to generate embeddings for.
    Returns:
        list[list[float]]: List of embeddings for each sentence.
    """
    embeddings = []
    
    # Flatten the list if input is a list of lists
    if isinstance(sentences[0], list):
        sentences = [item for sublist in sentences for item in sublist]
    for sentence in sentences:
        try:
            if not isinstance(sentence, str):
                logger.warning(f"Skipping non-string input: {sentence}")
                continue

            # Log the sentence being processed
            logger.info(f"Processing sentence: {sentence[:50]}...")

            # Truncate overly long sentences
            sentence = sentence[:512]

            # Tokenize the sentence
            input_data = tokenizer(
                sentence, 
                padding="longest", 
                truncation=True, 
                max_length=512, 
                return_tensors="pt"
            )
            input_data = {k: v.to(torch.device("cpu")) for k, v in input_data.items()}

            # Get model's last hidden state
            attention_mask = input_data["attention_mask"]
            last_hidden_state = model(**input_data)[0]

            # Compute the embeddings by averaging the hidden states
            last_hidden = last_hidden_state.masked_fill(~attention_mask[..., None].bool(), 0.0)
            sentence_embedding = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

            # Detach, convert to NumPy, and normalize
            detached_embedding = vector_linear(sentence_embedding).detach().cpu().numpy()
            normalized_embedding = normalize(detached_embedding, axis=1)

            embeddings.append(normalized_embedding[0].tolist())
            logger.info(f"Successfully generated embedding for: {sentence[:50]}...")

        except Exception as e:
            logger.error(f"Error while embedding sentence: {sentence}\n{e}")
            continue

    return embeddings

# Function to process and store embeddings
async def process_sentences_and_store(
    sentences: list[str], org_id: int, session: UserSession
) -> int:
    
    if not sentences:
        raise ValueError("No sentences provided for embedding.")

    successful_count = 0  # Initialize the count of successfully stored embeddings
    print("Sentence Count1:", len(sentences))

    try:
        # Generate embeddings using the transformer model
        embeddings = await get_embeddings_transformer(sentences)
        print("Embedding Count:", len(embeddings))
        if not embeddings:
            logger.error("No valid embeddings were generated.")
            return successful_count
        logger.info("Embeddings successfully generated.")

        if not session.is_active:
            session.begin()
        
        # Store embeddings and metadata in the database
        for idx, embedding in enumerate(embeddings):
            try:
                # Get the corresponding sentence based on the current index
                current_sentence = sentences[idx] if isinstance(sentences[idx], str) else str(sentences[idx])

                embedding_entry = OrgDataEmbedding(
                    metaData={"sentence": current_sentence},
                    embedding=embedding,
                    org_id=org_id
                )

                session.add(embedding_entry)
                successful_count += 1
                logger.info(f"Successfully stored embedding for sentence at index {idx}.")

            except Exception as e:
                logger.error(f"Error storing embedding for sentence at index {idx}: {str(e)}")
                continue

        if successful_count > 0:
            session.commit()
            logger.info(f"Successfully stored {successful_count} embeddings.")
        else:
            logger.error("No embeddings were stored in the database.")

    except Exception as e:
        logger.error(f"Error processing sentences: {str(e)}")
        session.rollback()
        raise

    return successful_count
