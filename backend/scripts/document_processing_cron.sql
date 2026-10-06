-- Enable Cron and pg_net in the Supabase dashboard before running this script.
-- Store these named secrets in Vault through the dashboard:
-- acquora_processing_endpoint = https://api.acquora.fr/api/v1/internal/document-processing
-- acquora_processing_secret = the backend's PROCESSING_CRON_SECRET
-- Secrets are resolved at execution, so rotation does not rewrite the job command.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM vault.secrets WHERE name = 'acquora_processing_endpoint')
     OR NOT EXISTS (SELECT 1 FROM vault.secrets WHERE name = 'acquora_processing_secret') THEN
    RAISE EXCEPTION 'Configure the two document-processing Vault secrets first';
  END IF;
END;
$$;

SELECT cron.schedule(
  'acquora-document-processing',
  '* * * * *',
  $job$
    SELECT net.http_post(
      url := (SELECT decrypted_secret FROM vault.decrypted_secrets
              WHERE name = 'acquora_processing_endpoint'),
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer ' ||
          (SELECT decrypted_secret FROM vault.decrypted_secrets
           WHERE name = 'acquora_processing_secret')
      ),
      body := '{}'::jsonb,
      timeout_milliseconds := 60000
    );
  $job$
);
