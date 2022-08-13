--
-- PostgreSQL database dump
--

-- Dumped from database version 13.2
-- Dumped by pg_dump version 13.2 (Debian 13.2-1.pgdg100+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: chat; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat (
    chat_id bigint NOT NULL,
    title character varying(128),
    admins bigint[],
    prev_winners bigint[],
    cur_winner bigint
);


ALTER TABLE public.chat OWNER TO postgres;

--
-- Name: chat_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_user (
    user_id bigint NOT NULL
);


ALTER TABLE public.chat_user OWNER TO postgres;

--
-- Name: in_chat; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.in_chat (
    user_id bigint NOT NULL,
    chat_id bigint NOT NULL
);


ALTER TABLE public.in_chat OWNER TO postgres;

--
-- Name: raffle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.raffle (
    chat_id bigint NOT NULL,
    start_date timestamp without time zone,
    end_date timestamp without time zone,
    entry_fee integer,
    dates timestamp without time zone[],
    entries character varying(128)[],
    amounts integer[]
);


ALTER TABLE public.raffle OWNER TO postgres;

--
-- Data for Name: cache_inval_bgw_job; Type: TABLE DATA; Schema: _timescaledb_cache; Owner: postgres
--

COPY _timescaledb_cache.cache_inval_bgw_job  FROM stdin;
\.


--
-- Data for Name: cache_inval_extension; Type: TABLE DATA; Schema: _timescaledb_cache; Owner: postgres
--

COPY _timescaledb_cache.cache_inval_extension  FROM stdin;
\.


--
-- Data for Name: cache_inval_hypertable; Type: TABLE DATA; Schema: _timescaledb_cache; Owner: postgres
--

COPY _timescaledb_cache.cache_inval_hypertable  FROM stdin;
\.


--
-- Data for Name: hypertable; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.hypertable (id, schema_name, table_name, associated_schema_name, associated_table_prefix, num_dimensions, chunk_sizing_func_schema, chunk_sizing_func_name, chunk_target_size, compression_state, compressed_hypertable_id, replication_factor) FROM stdin;
\.


--
-- Data for Name: chunk; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.chunk (id, hypertable_id, schema_name, table_name, compressed_chunk_id, dropped) FROM stdin;
\.


--
-- Data for Name: dimension; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.dimension (id, hypertable_id, column_name, column_type, aligned, num_slices, partitioning_func_schema, partitioning_func, interval_length, integer_now_func_schema, integer_now_func) FROM stdin;
\.


--
-- Data for Name: dimension_slice; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.dimension_slice (id, dimension_id, range_start, range_end) FROM stdin;
\.


--
-- Data for Name: chunk_constraint; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.chunk_constraint (chunk_id, dimension_slice_id, constraint_name, hypertable_constraint_name) FROM stdin;
\.


--
-- Data for Name: chunk_data_node; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.chunk_data_node (chunk_id, node_chunk_id, node_name) FROM stdin;
\.


--
-- Data for Name: chunk_index; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.chunk_index (chunk_id, index_name, hypertable_id, hypertable_index_name) FROM stdin;
\.


--
-- Data for Name: compression_chunk_size; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.compression_chunk_size (chunk_id, compressed_chunk_id, uncompressed_heap_size, uncompressed_toast_size, uncompressed_index_size, compressed_heap_size, compressed_toast_size, compressed_index_size, numrows_pre_compression, numrows_post_compression) FROM stdin;
\.


--
-- Data for Name: continuous_agg; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.continuous_agg (mat_hypertable_id, raw_hypertable_id, user_view_schema, user_view_name, partial_view_schema, partial_view_name, bucket_width, direct_view_schema, direct_view_name, materialized_only) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_hypertable_invalidation_log; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.continuous_aggs_hypertable_invalidation_log (hypertable_id, lowest_modified_value, greatest_modified_value) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_invalidation_threshold; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.continuous_aggs_invalidation_threshold (hypertable_id, watermark) FROM stdin;
\.


--
-- Data for Name: continuous_aggs_materialization_invalidation_log; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.continuous_aggs_materialization_invalidation_log (materialization_id, lowest_modified_value, greatest_modified_value) FROM stdin;
\.


--
-- Data for Name: hypertable_compression; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.hypertable_compression (hypertable_id, attname, compression_algorithm_id, segmentby_column_index, orderby_column_index, orderby_asc, orderby_nullsfirst) FROM stdin;
\.


--
-- Data for Name: hypertable_data_node; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.hypertable_data_node (hypertable_id, node_hypertable_id, node_name, block_chunks) FROM stdin;
\.


--
-- Data for Name: metadata; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.metadata (key, value, include_in_telemetry) FROM stdin;
exported_uuid	bfd1f49e-9c98-422f-bb23-d89dbe061b6c	t
\.


--
-- Data for Name: remote_txn; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.remote_txn (data_node_name, remote_transaction_id) FROM stdin;
\.


--
-- Data for Name: tablespace; Type: TABLE DATA; Schema: _timescaledb_catalog; Owner: postgres
--

COPY _timescaledb_catalog.tablespace (id, hypertable_id, tablespace_name) FROM stdin;
\.


--
-- Data for Name: bgw_job; Type: TABLE DATA; Schema: _timescaledb_config; Owner: postgres
--

COPY _timescaledb_config.bgw_job (id, application_name, schedule_interval, max_runtime, max_retries, retry_period, proc_schema, proc_name, owner, scheduled, hypertable_id, config) FROM stdin;
\.


--
-- Data for Name: chat; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat (chat_id, title, admins, prev_winners, cur_winner) FROM stdin;
-639070190	Testing 2 🍌	{1612418267}	{NULL}	\N
-627122056	Testing	{1612418267}	{NULL}	1612418267
-707334379	Test 3	{1612418267}	{NULL}	1612418267
\.


--
-- Data for Name: chat_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_user (user_id) FROM stdin;
1612418267
\.


--
-- Data for Name: in_chat; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.in_chat (user_id, chat_id) FROM stdin;
1612418267	-639070190
1612418267	-707334379
1612418267	-627122056
\.


--
-- Data for Name: raffle; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.raffle (chat_id, start_date, end_date, entry_fee, dates, entries, amounts) FROM stdin;
-639070190	2022-08-08 16:00:00	2022-08-12 16:00:00	100	{"2022-08-08 20:14:06.617","2022-08-08 20:07:39.102","2022-08-08 20:01:53.649","2022-08-08 17:52:50.366","2022-08-08 17:09:25.712","2022-08-08 17:06:18.625"}	{"Lauri Lappalainen","Petrus Asikainen","Mikko Juhani Juusti","Sami Juvaste","EMILIA REPO","Suvi Zitting"}	{100,100,100,100,1000,100}
-627122056	2022-08-08 16:00:00	2022-08-12 16:00:00	100	{"2022-08-08 20:14:06.617","2022-08-08 20:07:39.102","2022-08-08 20:01:53.649","2022-08-08 17:52:50.366","2022-08-08 17:09:25.712","2022-08-08 17:06:18.625"}	{"Lauri Lappalainen","Petrus Asikainen","Mikko Juhani Juusti","Sami Juvaste","EMILIA REPO","Suvi Zitting"}	{100,100,100,100,1000,100}
-707334379	2022-08-08 16:00:00	2022-08-12 16:00:00	100	{"2022-08-08 20:14:06.617","2022-08-08 20:07:39.102","2022-08-08 20:01:53.649","2022-08-08 17:52:50.366","2022-08-08 17:09:25.712","2022-08-08 17:06:18.625"}	{"Lauri Lappalainen","Petrus Asikainen","Mikko Juhani Juusti","Sami Juvaste","EMILIA REPO","Suvi Zitting"}	{100,100,100,100,1000,100}
\.


--
-- Name: chunk_constraint_name; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: postgres
--

SELECT pg_catalog.setval('_timescaledb_catalog.chunk_constraint_name', 1, false);


--
-- Name: chunk_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: postgres
--

SELECT pg_catalog.setval('_timescaledb_catalog.chunk_id_seq', 1, false);


--
-- Name: dimension_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: postgres
--

SELECT pg_catalog.setval('_timescaledb_catalog.dimension_id_seq', 1, false);


--
-- Name: dimension_slice_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: postgres
--

SELECT pg_catalog.setval('_timescaledb_catalog.dimension_slice_id_seq', 1, false);


--
-- Name: hypertable_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_catalog; Owner: postgres
--

SELECT pg_catalog.setval('_timescaledb_catalog.hypertable_id_seq', 1, false);


--
-- Name: bgw_job_id_seq; Type: SEQUENCE SET; Schema: _timescaledb_config; Owner: postgres
--

SELECT pg_catalog.setval('_timescaledb_config.bgw_job_id_seq', 1000, false);


--
-- Name: chat chat_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat
    ADD CONSTRAINT chat_pkey PRIMARY KEY (chat_id);


--
-- Name: chat_user chat_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_user
    ADD CONSTRAINT chat_user_pkey PRIMARY KEY (user_id);


--
-- Name: in_chat in_chat_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.in_chat
    ADD CONSTRAINT in_chat_pkey PRIMARY KEY (user_id, chat_id);


--
-- Name: raffle raffle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.raffle
    ADD CONSTRAINT raffle_pkey PRIMARY KEY (chat_id);


--
-- Name: in_chat in_chat_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.in_chat
    ADD CONSTRAINT in_chat_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chat(chat_id);


--
-- Name: in_chat in_chat_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.in_chat
    ADD CONSTRAINT in_chat_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.chat_user(user_id);


--
-- Name: raffle raffle_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.raffle
    ADD CONSTRAINT raffle_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chat(chat_id);


--
-- PostgreSQL database dump complete
--

