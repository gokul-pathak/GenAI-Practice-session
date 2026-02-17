-- create document and document chunks

create or replace function match_chunks(
  query_embedding vector(1024),
  match_count int,
  filter_document uuid
)
returns table (
  id uuid,
  content text,
  similarity float
)
language sql stable
as $$
  select
    id,
    content,
    1 - (embedding <=> query_embedding) as similarity
  from document_chunks
  where document_id = filter_document
  order by embedding <=> query_embedding
  limit match_count;
$$;


-- 🔎 Similarity Search Function

create or replace function match_chunks(
  query_embedding vector(1024),
  match_count int,
  filter_document uuid
)
returns table (
  id uuid,
  content text,
  similarity float
)
language sql stable
as $$
  select
    id,
    content,
    1 - (embedding <=> query_embedding) as similarity
  from document_chunks
  where document_id = filter_document
  order by embedding <=> query_embedding
  limit match_count;
$$;
