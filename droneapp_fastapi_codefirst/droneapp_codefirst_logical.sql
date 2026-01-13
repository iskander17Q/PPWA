--
-- PostgreSQL database dump
--

\restrict kjyfqF7PxVBagcw1AkR1r2O6egTDj01ErMpun1pp6nav0suUSXFZcVeIJ1JFpLZ

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: input_images; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.input_images (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    filename character varying(255) NOT NULL,
    storage_path text NOT NULL,
    uploaded_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.input_images OWNER TO postgres;

--
-- Name: input_images_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.input_images_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.input_images_id_seq OWNER TO postgres;

--
-- Name: input_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.input_images_id_seq OWNED BY public.input_images.id;


--
-- Name: output_artifacts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.output_artifacts (
    id bigint NOT NULL,
    processing_run_id bigint NOT NULL,
    artifact_type character varying(20) NOT NULL,
    storage_path text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.output_artifacts OWNER TO postgres;

--
-- Name: output_artifacts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.output_artifacts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.output_artifacts_id_seq OWNER TO postgres;

--
-- Name: output_artifacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.output_artifacts_id_seq OWNED BY public.output_artifacts.id;


--
-- Name: processing_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.processing_runs (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    input_image_id bigint NOT NULL,
    index_type character varying(10) NOT NULL,
    status character varying(10) DEFAULT 'QUEUED'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.processing_runs OWNER TO postgres;

--
-- Name: processing_runs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.processing_runs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.processing_runs_id_seq OWNER TO postgres;

--
-- Name: processing_runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.processing_runs_id_seq OWNED BY public.processing_runs.id;


--
-- Name: reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reports (
    id bigint NOT NULL,
    run_id bigint NOT NULL,
    pdf_path text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.reports OWNER TO postgres;

--
-- Name: reports_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reports_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reports_id_seq OWNER TO postgres;

--
-- Name: reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reports_id_seq OWNED BY public.reports.id;


--
-- Name: subscription_plans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subscription_plans (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    free_attempts_limit integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.subscription_plans OWNER TO postgres;

--
-- Name: subscription_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.subscription_plans_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subscription_plans_id_seq OWNER TO postgres;

--
-- Name: subscription_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.subscription_plans_id_seq OWNED BY public.subscription_plans.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    name character varying(120),
    role character varying(10) DEFAULT 'USER'::character varying NOT NULL,
    plan_id bigint NOT NULL,
    free_attempts_used bigint DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    phone character varying(30),
    last_login_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: input_images id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.input_images ALTER COLUMN id SET DEFAULT nextval('public.input_images_id_seq'::regclass);


--
-- Name: output_artifacts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.output_artifacts ALTER COLUMN id SET DEFAULT nextval('public.output_artifacts_id_seq'::regclass);


--
-- Name: processing_runs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processing_runs ALTER COLUMN id SET DEFAULT nextval('public.processing_runs_id_seq'::regclass);


--
-- Name: reports id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reports ALTER COLUMN id SET DEFAULT nextval('public.reports_id_seq'::regclass);


--
-- Name: subscription_plans id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscription_plans ALTER COLUMN id SET DEFAULT nextval('public.subscription_plans_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
0002_add_user_phone_report
\.


--
-- Data for Name: input_images; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.input_images (id, user_id, filename, storage_path, uploaded_at) FROM stdin;
1	2	sample.jpg	/tmp/sample.jpg	2026-01-12 15:12:49.247434
2	2	sample.jpg	/tmp/sample.jpg	2026-01-12 15:45:13.26864
\.


--
-- Data for Name: output_artifacts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.output_artifacts (id, processing_run_id, artifact_type, storage_path, created_at) FROM stdin;
1	1	VISUAL_PNG	/tmp/out.png	2026-01-12 15:12:49.247434
2	2	VISUAL_PNG	/tmp/out.png	2026-01-12 15:45:13.26864
\.


--
-- Data for Name: processing_runs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.processing_runs (id, user_id, input_image_id, index_type, status, created_at) FROM stdin;
1	2	1	NDVI	SUCCESS	2026-01-12 15:12:49.247434
2	2	2	NDVI	SUCCESS	2026-01-12 15:45:13.26864
\.


--
-- Data for Name: reports; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reports (id, run_id, pdf_path, created_at) FROM stdin;
\.


--
-- Data for Name: subscription_plans; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.subscription_plans (id, name, free_attempts_limit, created_at) FROM stdin;
1	Free	2	2026-01-12 15:12:49.247434
2	Pro	999999	2026-01-12 15:12:49.247434
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, password_hash, name, role, plan_id, free_attempts_used, is_active, created_at, phone, last_login_at) FROM stdin;
1	admin@droneapp.local	fakehash	Admin	ADMIN	1	0	t	2026-01-12 15:12:49.247434	\N	\N
2	user@droneapp.local	fakehash	User	USER	1	1	t	2026-01-12 15:12:49.247434	\N	\N
\.


--
-- Name: input_images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.input_images_id_seq', 2, true);


--
-- Name: output_artifacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.output_artifacts_id_seq', 2, true);


--
-- Name: processing_runs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.processing_runs_id_seq', 2, true);


--
-- Name: reports_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reports_id_seq', 1, false);


--
-- Name: subscription_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subscription_plans_id_seq', 8, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 5, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: input_images input_images_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.input_images
    ADD CONSTRAINT input_images_pkey PRIMARY KEY (id);


--
-- Name: output_artifacts output_artifacts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.output_artifacts
    ADD CONSTRAINT output_artifacts_pkey PRIMARY KEY (id);


--
-- Name: processing_runs processing_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processing_runs
    ADD CONSTRAINT processing_runs_pkey PRIMARY KEY (id);


--
-- Name: reports reports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (id);


--
-- Name: subscription_plans subscription_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subscription_plans
    ADD CONSTRAINT subscription_plans_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: input_images input_images_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.input_images
    ADD CONSTRAINT input_images_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: output_artifacts output_artifacts_processing_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.output_artifacts
    ADD CONSTRAINT output_artifacts_processing_run_id_fkey FOREIGN KEY (processing_run_id) REFERENCES public.processing_runs(id);


--
-- Name: processing_runs processing_runs_input_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processing_runs
    ADD CONSTRAINT processing_runs_input_image_id_fkey FOREIGN KEY (input_image_id) REFERENCES public.input_images(id);


--
-- Name: processing_runs processing_runs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processing_runs
    ADD CONSTRAINT processing_runs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: reports reports_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.processing_runs(id);


--
-- Name: users users_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.subscription_plans(id);


--
-- PostgreSQL database dump complete
--

\unrestrict kjyfqF7PxVBagcw1AkR1r2O6egTDj01ErMpun1pp6nav0suUSXFZcVeIJ1JFpLZ

