from typing import Any, Dict, List, Optional
import structlog

from app.rag.chunking import RecursiveTextChunker
from app.rag.embeddings.base import EmbeddingProviderBase
from app.rag.embeddings.factory import EmbeddingProviderFactory
from app.rag.retrieval import HybridSearchEngine
from app.rag.store import VectorKnowledgeStore

logger = structlog.get_logger()

DEFAULT_FINTECH_POLICIES = [
    {
        "doc_id": "pol_refunds_tat",
        "title": "Refund Timelines and Turnaround Time (TAT) Guidelines",
        "category": "refunds",
        "content": """# Refund Timelines and Turnaround Time (TAT) Guidelines

## Overview
This policy governs turnaround times for transaction refunds, reversals, and settlement failures across UPI, Cards, NetBanking, and Wallets in accordance with RBI Harmonisation of Turnaround Time guidelines.

## Method-Specific Refund Timelines
1. UPI Payments: Immediate to T+1 business days. In case of network drops or timeout, auto-reversals take up to T+3 business days.
2. Debit and Credit Cards: 5 to 7 working days, depending on the customer's card-issuing bank and payment settlement cycle.
3. NetBanking Transactions: 2 to 4 working days for bank-to-bank settlement.
4. Digital Wallet Balances: Instant refund (within 2 hours) back to the linked wallet balance.

## RBI Penalty for Delayed Reversal
Under RBI guidelines (DPSS.CO.PD No.629/02.01.014/2019-20), if a failed transaction debit is not reversed within the prescribed TAT (T+5 days for card transactions and T+1 for UPI), the acquiring bank or merchant shall pay compensation of ₹100 per day of delay to the customer.

## Supervisor Review & HITL Threshold
Any refund request exceeding ₹10,000 must be reviewed and authorized by a senior operations supervisor before funds are released. This safeguard prevents fraudulent refund extraction and systemic overdrafts.
""",
    },
    {
        "doc_id": "pol_account_security",
        "title": "Account Freeze and Risk Intervention Policy",
        "category": "account",
        "content": """# Account Freeze and Risk Intervention Policy

## Conditions for Account Freeze
An account may be frozen or put under debit restrictions under the following conditions:
1. Automated Fraud Detection: Risk score exceeding 85/100, rapid velocity of transactions to blacklisted VPAs, or geo-velocity anomalies.
2. Regulatory / Cybercrime Notices: Orders issued by LEAs (Law Enforcement Agencies) or cybercrime cells.
3. Repeated Authentication Failures: More than 5 consecutive invalid MPIN or OTP entries.
4. Pending Re-KYC: Failure to update KYC documents within statutory compliance deadlines.

## Impact on Account Operations
- Full Freeze: Both incoming credits and outgoing debits are restricted.
- Debit Freeze: The account can receive inward credits (e.g. salary, transfers) but cannot initiate debits, UPI transfers, or ATM withdrawals.

## Unfreeze Procedures
To unfreeze an account:
1. The customer must undergo Video KYC (V-KYC) verification through the mobile application.
2. If frozen by automated risk controls, the risk operations team will review the last 5 transactions and request proof of identity (PAN card) and selfie verification.
3. A support ticket is logged with High priority, and customer escalation is assigned within 4 hours.
""",
    },
    {
        "doc_id": "pol_chargebacks_disputes",
        "title": "Unauthorized Transactions and Customer Liability Policy",
        "category": "fraud",
        "content": """# Unauthorized Transactions and Customer Liability Policy

## Customer Liability Framework (RBI Circular DBR.No.Leg.BC.78/09.07.005/2017-18)
Customer liability in unauthorized electronic banking transactions is categorized as follows:

1. Zero Liability:
   - Contributory fraud, negligence, or deficiency on the part of the bank (whether reported by customer or not).
   - Third-party breach where deficiency lies neither with bank nor customer, and customer notifies the bank within 3 working days of receiving transaction alert.

2. Limited Liability:
   - If negligence lies with customer (e.g. sharing credentials, OTP, PIN), customer bears entire loss until unauthorized transaction is reported to the bank. Any loss occurring after reporting is borne by the bank.
   - If third-party breach and customer delay in reporting is 4 to 7 working days, maximum customer liability is capped at ₹10,000 for standard accounts (₹5,000 for Basic Savings Bank Deposit Accounts).

3. Beyond 7 Working Days:
   - Customer liability is determined as per the bank's internal board-approved policy.
""",
    },
    {
        "doc_id": "pol_safety_security",
        "title": "Safety Guidelines, Phishing Protection and Secret Sharing",
        "category": "security",
        "content": """# Safety Guidelines, Phishing Protection and Secret Sharing

## Confidential Credentials
Bank and support agents will NEVER under any circumstances ask customers for:
- UPI PIN or ATM PIN
- Card CVV (Card Verification Value)
- One-Time Password (OTP)
- Internet banking passwords or token codes

## Common Fraud Patterns & Red Flags
1. Receive Money Fraud: UPI PIN is required ONLY to send or deduct money from an account. No PIN or approval is ever needed to receive money into an account.
2. Screen Sharing Apps: Fraudsters posing as customer care trick users into downloading remote access apps (AnyDesk, TeamViewer). Never install third-party apps on representative instructions.
3. Fake Customer Care Numbers: Always verify support phone numbers and URLs from the official application.

## Incident Escalation
If a customer reports unauthorized access or suspect phishing, agents must immediately freeze linked debit cards and escalate the ticket to the Human Fraud Response Team.
""",
    },
]


class PolicyKnowledgeService:
    """High-level service managing document ingestion and hybrid policy search."""

    def __init__(
        self,
        vector_store: Optional[VectorKnowledgeStore] = None,
        embedding_provider: Optional[EmbeddingProviderBase] = None,
    ):
        self.vector_store = vector_store or VectorKnowledgeStore()
        if embedding_provider is not None:
            self.embedding_provider = embedding_provider
        elif not settings.GEMINI_API_KEY:
            from app.rag.embeddings.mock import MockEmbeddingProvider
            self.embedding_provider = MockEmbeddingProvider()
        else:
            self.embedding_provider = EmbeddingProviderFactory.create()

        self.chunker = RecursiveTextChunker(chunk_size=800, chunk_overlap=100)
        self.search_engine = HybridSearchEngine(
            vector_store=self.vector_store,
            embedding_provider=self.embedding_provider,
        )

    async def ingest_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Chunk, embed, and index a policy document."""
        base_meta = dict(metadata or {})
        base_meta.update({"title": title, "category": category})

        chunks = self.chunker.chunk_document(doc_id=doc_id, text=content, base_metadata=base_meta)
        if not chunks:
            return 0

        chunk_texts = [c.text for c in chunks]
        embeddings = await self.embedding_provider.embed_batch(chunk_texts)

        self.vector_store.add_chunks(chunks=chunks, embeddings=embeddings)
        self.search_engine.refresh_index()

        logger.info(
            "document_ingested",
            doc_id=doc_id,
            title=title,
            chunks_count=len(chunks),
        )
        return len(chunks)

    async def seed_default_policies(self) -> int:
        """Seed pre-configured standard banking policies into the knowledge base."""
        total_chunks = 0
        for doc in DEFAULT_FINTECH_POLICIES:
            count = await self.ingest_document(
                doc_id=doc["doc_id"],
                title=doc["title"],
                content=doc["content"],
                category=doc["category"],
            )
            total_chunks += count
        return total_chunks

    async def search_policies(
        self,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search policy knowledge base using hybrid search."""
        return await self.search_engine.search(query=query, top_k=top_k, category=category)
