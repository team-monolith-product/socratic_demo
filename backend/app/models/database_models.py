"""SQLAlchemy database models with cross-database compatibility."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class Teacher(Base):
    """Teacher model."""
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    fingerprint: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session",
        back_populates="teacher",
        cascade="all, delete-orphan"
    )


class Session(Base):
    """Session model."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    teacher_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(10), default="normal")
    show_score: Mapped[bool] = mapped_column(Boolean, default=True)
    time_limit: Mapped[Optional[int]] = mapped_column(Integer)
    max_students: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="sessions")
    students: Mapped[List["Student"]] = relationship(
        "Student",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class Student(Base):
    """Student model."""
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    conversation_turns: Mapped[int] = mapped_column(Integer, default=0)
    current_score: Mapped[int] = mapped_column(Integer, default=0)
    depth_score: Mapped[int] = mapped_column(Integer, default=0)
    breadth_score: Mapped[int] = mapped_column(Integer, default=0)
    application_score: Mapped[int] = mapped_column(Integer, default=0)
    metacognition_score: Mapped[int] = mapped_column(Integer, default=0)
    engagement_score: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="students")
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="student",
        cascade="all, delete-orphan"
    )


class Message(Base):
    """Message model."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(10), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="messages")
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="message",
        cascade="all, delete-orphan"
    )


class Score(Base):
    """Score model for tracking student response evaluations."""
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Socratic dimension scores (0-100)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    depth_score: Mapped[int] = mapped_column(Integer, nullable=False)
    breadth_score: Mapped[int] = mapped_column(Integer, nullable=False)
    application_score: Mapped[int] = mapped_column(Integer, nullable=False)
    metacognition_score: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Evaluation metadata
    evaluation_data: Mapped[Optional[dict]] = mapped_column(JSON)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="scores")
    student: Mapped["Student"] = relationship("Student", back_populates="scores")
    session: Mapped["Session"] = relationship("Session", back_populates="scores")



