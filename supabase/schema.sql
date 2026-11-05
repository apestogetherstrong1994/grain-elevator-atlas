-- Grain Elevator Atlas: shared BD tracking
-- Run once in Supabase: Dashboard -> SQL Editor -> New query -> paste -> Run.
-- Safe to re-run: tables/policies are created only if missing, and seed rows upsert.

-- Who may read and write: anyone signed in with an @lumaril.com address,
-- plus anyone listed in the team table (e.g. personal addresses).
create table if not exists public.team (
  email      text primary key check (email = lower(email)),
  name       text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.tracking (
  fid         text primary key,                                   -- facility id from elevators.json, e.g. ND-8903b2be
  owner_email text references public.team(email) on update cascade on delete set null,
  status      text not null default 'none'
              check (status in ('none','research','contacted','convo','visit','pilot','nofit')),
  updated_at  timestamptz not null default now(),
  updated_by  text
);

create table if not exists public.notes (
  id           uuid primary key default gen_random_uuid(),
  fid          text not null,
  body         text not null check (char_length(body) between 1 and 4000),
  author_email text not null default lower(coalesce(auth.jwt() ->> 'email', '')),
  created_at   timestamptz not null default now()
);
create index if not exists notes_fid_idx on public.notes (fid);

create or replace function public.is_member() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce(lower(auth.jwt() ->> 'email') like '%@lumaril.com', false)
      or exists (select 1 from public.team t where t.email = lower(auth.jwt() ->> 'email'));
$$;
grant execute on function public.is_member() to authenticated;

create or replace function public.stamp_tracking() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  new.updated_at := now();
  new.updated_by := lower(coalesce(auth.jwt() ->> 'email', new.updated_by));
  return new;
end $$;
drop trigger if exists tracking_stamp on public.tracking;
create trigger tracking_stamp before insert or update on public.tracking
  for each row execute function public.stamp_tracking();

alter table public.team     enable row level security;
alter table public.tracking enable row level security;
alter table public.notes    enable row level security;

do $$ begin
  -- team: members read and add/rename teammates
  if not exists (select 1 from pg_policies where tablename='team' and policyname='team_read') then
    create policy team_read   on public.team for select to authenticated using (public.is_member());
    create policy team_insert on public.team for insert to authenticated with check (public.is_member());
    create policy team_update on public.team for update to authenticated using (public.is_member()) with check (public.is_member());
  end if;
  -- tracking: members read and write
  if not exists (select 1 from pg_policies where tablename='tracking' and policyname='tracking_read') then
    create policy tracking_read   on public.tracking for select to authenticated using (public.is_member());
    create policy tracking_insert on public.tracking for insert to authenticated with check (public.is_member());
    create policy tracking_update on public.tracking for update to authenticated using (public.is_member()) with check (public.is_member());
  end if;
  -- notes: members read and add; authors delete their own
  if not exists (select 1 from pg_policies where tablename='notes' and policyname='notes_read') then
    create policy notes_read   on public.notes for select to authenticated using (public.is_member());
    create policy notes_insert on public.notes for insert to authenticated
      with check (public.is_member() and author_email = lower(auth.jwt() ->> 'email'));
    create policy notes_delete on public.notes for delete to authenticated
      using (author_email = lower(auth.jwt() ->> 'email'));
  end if;
end $$;

-- live updates for open browsers
do $$ begin
  begin alter publication supabase_realtime add table public.team;     exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.tracking; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.notes;    exception when duplicate_object then null; end;
end $$;
