-- Onward — tiny follow-up: incident_intelligence.provider still had its
-- original 'anthropic' default from before the Gemini switch (Phase 3 cost
-- update). Never actually relied upon — every insert (WF-02) sets it
-- explicitly — but a stale default is misleading to read. Run in the
-- Supabase SQL Editor whenever convenient; nothing depends on this.

alter table incident_intelligence alter column provider drop default;
