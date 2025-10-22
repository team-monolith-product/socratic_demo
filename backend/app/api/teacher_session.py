from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from app.models.session_models import (
    SessionCreateRequest, SessionCreateResponse, SessionConfig,
    TeacherSessionsResponse, SessionDetailsResponse, SessionJoinRequest,
    SessionJoinResponse, QRCodeInfo, SessionInfo
)
from app.models.request_models import SessionChatRequest, SessionChatResponse
from app.services.session_service import get_session_service
from app.services.qr_service import get_qr_service
from app.services.socratic_service import SocraticService
from app.services.storage_service import get_storage_service
from app.services.socratic_assessment_service import get_socratic_assessment_service
from datetime import datetime
import io

router = APIRouter()

def get_socratic_service():
    return SocraticService()

@router.post("/teacher/sessions", response_model=SessionCreateResponse)
async def create_session(request: Request, config: SessionConfig):
    """Create new teaching session"""
    try:
        session_service = get_session_service()
        qr_service = get_qr_service()

        # Generate teacher fingerprint from request headers
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # Use frontend URL from config for student access
        from app.core.config import get_settings
        settings = get_settings()
        frontend_url = settings.frontend_url

        # Create session
        session_result = await session_service.create_session(config, teacher_fingerprint, frontend_url)
        session_id = session_result['session_id']
        session_data = session_result['session_data']
        session_url = session_result['session_url']

        # Generate QR code
        qr_result = qr_service.generate_qr_code(session_url)
        if not qr_result['success']:
            raise HTTPException(status_code=500, detail="Failed to generate QR code")

        # Prepare response
        session_info = SessionInfo(
            id=session_id,
            config=config,
            status=session_data['status'],
            created_at=session_data['created_at'],
            expires_at=session_data['expires_at']
        )

        qr_info = QRCodeInfo(
            url=session_url,
            image_data=qr_result['image_data'],
            download_url=f"/api/v1/qr/{session_id}.png"
        )

        return SessionCreateResponse(
            success=True,
            session=session_info,
            qr_code=qr_info
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teacher/sessions", response_model=TeacherSessionsResponse)
async def get_teacher_sessions(request: Request):
    """Get all sessions for teacher (identified by browser fingerprint)"""
    try:
        session_service = get_session_service()

        # Generate teacher fingerprint
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # Get sessions
        sessions = await session_service.get_teacher_sessions(teacher_fingerprint)

        # Convert datetime objects to ISO strings with timezone info
        for session in sessions:
            for field in ['created_at', 'expires_at', 'last_activity', 'ended_at']:
                if field in session and hasattr(session[field], 'isoformat'):
                    session[field] = session[field].isoformat()

            # Also convert datetime objects in live_stats if any
            if 'live_stats' in session and 'recent_activities' in session['live_stats']:
                for activity in session['live_stats']['recent_activities']:
                    if 'timestamp' in activity and hasattr(activity['timestamp'], 'isoformat'):
                        activity['timestamp'] = activity['timestamp'].isoformat()

        # Calculate summary stats
        total_sessions = len(sessions)
        total_students = sum(s.get('live_stats', {}).get('total_joined', 0) for s in sessions)

        # Calculate average score from all sessions
        if sessions:
            avg_score = sum(s.get('live_stats', {}).get('average_score', 0) for s in sessions) / len(sessions)
        else:
            avg_score = 0

        summary = {
            'total_sessions': total_sessions,
            'total_students': total_students,
            'average_score': round(avg_score, 1)
        }

        return TeacherSessionsResponse(
            sessions=sessions,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teacher/sessions/{session_id}", response_model=SessionDetailsResponse)
async def get_session_details(session_id: str, request: Request):
    """Get detailed session information for monitoring"""
    print(f"🔍 GET /teacher/sessions/{session_id}")
    print(f"🔍 Request headers: {dict(request.headers)}")

    try:
        session_service = get_session_service()

        # Generate teacher fingerprint
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # Get session details
        session_details = await session_service.get_session_details(session_id, teacher_fingerprint)

        if not session_details:
            print(f"❌ Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        session_data = session_details['session']
        students = session_details['students']

        # Convert datetime objects to ISO strings with timezone info
        for field in ['created_at', 'expires_at', 'last_activity', 'ended_at']:
            if field in session_data and hasattr(session_data[field], 'isoformat'):
                session_data[field] = session_data[field].isoformat()

        # Convert datetime objects in students
        for student in students:
            for field in ['last_activity', 'joined_at']:
                if field in student and hasattr(student[field], 'isoformat'):
                    student[field] = student[field].isoformat()

        # Prepare response
        session_info = SessionInfo(
            id=session_data['id'],
            config=SessionConfig(**session_data['config']),
            status=session_data['status'],
            created_at=session_data['created_at'],
            expires_at=session_data['expires_at']
        )

        live_stats = session_data['live_stats']

        return SessionDetailsResponse(
            session=session_info,
            live_stats=live_stats,
            students=students
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teacher/sessions/{session_id}/end")
async def end_session(session_id: str, request: Request):
    """End a session"""
    try:
        session_service = get_session_service()

        # Generate teacher fingerprint
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # End session
        final_stats = await session_service.end_session(session_id, teacher_fingerprint)
        if final_stats is None:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "final_stats": final_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/teacher/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    """Delete a session"""
    try:
        session_service = get_session_service()

        # Generate teacher fingerprint
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # Delete session
        success = await session_service.delete_session(session_id, teacher_fingerprint)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "message": "세션이 삭제되었습니다"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session info for student (public endpoint)"""
    try:
        session_service = get_session_service()
        storage_service = get_storage_service()

        # Check if session exists in database
        db_session = await storage_service.get_session_by_id(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        config = SessionConfig(
            title=db_session.title,
            topic=db_session.topic,
            description=db_session.description,
            difficulty=db_session.difficulty,
            show_score=db_session.show_score,
            time_limit=db_session.time_limit,
            max_students=db_session.max_students
        )

        return {
            "session": {
                "id": session_id,
                "topic": config.topic,
                "description": config.description,
                "difficulty": config.difficulty,
                "show_score": config.show_score,
                "is_active": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/{session_id}/join", response_model=SessionJoinResponse)
async def join_session(session_id: str, request: SessionJoinRequest, http_request: Request):
    """Student joins a session"""
    try:
        session_service = get_session_service()
        socratic_service = get_socratic_service()

        # Join session (token + name-based matching for returning students)
        join_result = await session_service.join_session(session_id, request.student_name, request.student_token)
        if not join_result:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        # Check if join_result contains an error
        if 'error' in join_result:
            raise HTTPException(status_code=400, detail=join_result['message'])

        student_id = join_result['student_id']
        session_config = join_result['session_config']
        is_returning = join_result.get('is_returning', False)

        # Generate initial message only for new students
        if not is_returning:
            initial_message = await socratic_service.generate_initial_message(session_config.topic)

            # Save initial AI message to database
            storage_service = get_storage_service()
            try:
                print(f"💬 Saving initial AI message for student {student_id}: {initial_message[:50]}...")
                result = await storage_service.save_message(
                    session_id=session_id,
                    student_id=student_id,
                    content=initial_message,
                    message_type="assistant"
                )
                print(f"✅ Initial AI message saved successfully: {result}")
            except Exception as e:
                print(f"❌ Warning: Could not save initial AI message: {e}")
        else:
            # For returning students, we won't show a separate initial message
            # The frontend will load previous chat history instead
            initial_message = ""

        # Get current score for returning students
        current_score = join_result.get('current_score', 0)

        return SessionJoinResponse(
            success=True,
            student_id=student_id,
            student_token=join_result['student_token'],
            session_config=session_config,
            initial_message=initial_message,
            understanding_score=current_score
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qr/{session_id}.png")
async def download_qr_code(session_id: str, request: Request):
    """Download QR code image"""
    try:
        session_service = get_session_service()
        qr_service = get_qr_service()
        storage_service = get_storage_service()

        # Check if session exists in database
        db_session = await storage_service.get_session_by_id(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Generate QR code for download (larger size) - use Vercel frontend URL
        base_url = "https://socratic-nine.vercel.app"
        session_url = f"{base_url}/s/{session_id}"

        qr_data = qr_service.get_qr_download_data(session_url, size=400)

        # Return as image response
        return StreamingResponse(
            io.BytesIO(qr_data),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=session_{session_id}.png"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/{session_id}/chat", response_model=SessionChatResponse)
async def session_chat(session_id: str, request: SessionChatRequest):
    """Handle chat message within a session and record to database"""
    try:
        session_service = get_session_service()
        socratic_service = get_socratic_service()
        assessment_service = get_socratic_assessment_service()
        storage_service = get_storage_service()

        # Verify session exists in database
        db_session = await storage_service.get_session_by_id(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify student is part of this session
        db_student = await storage_service.get_student_by_id(request.student_id)
        if not db_student or db_student.session_id != session_id:
            raise HTTPException(status_code=403, detail="Student not authorized for this session")

        # Get session configuration
        config = SessionConfig(
            title=db_session.title,
            topic=db_session.topic,
            description=db_session.description,
            difficulty=db_session.difficulty,
            show_score=db_session.show_score,
            time_limit=db_session.time_limit,
            max_students=db_session.max_students
        )

        # Get student's chat history from database if available
        messages = []
        # Get previous messages for this student in this session
        try:
            stored_messages = await storage_service.get_student_messages(session_id, request.student_id)
            # Reverse the order since we get them newest-first from DB, but need oldest-first for conversation context
            stored_messages.reverse()
            messages = [{"role": msg["message_type"], "content": msg["content"]} for msg in stored_messages]
        except Exception as e:
            print(f"Warning: Could not load message history: {e}")

        # Add the new user message
        messages.append({"role": "user", "content": request.message})

        # Store user message in database
        try:
            await storage_service.save_message(
                session_id=session_id,
                student_id=request.student_id,
                content=request.message,
                message_type="user"
            )
        except Exception as e:
            print(f"Warning: Could not save user message: {e}")

        # Generate AI response
        socratic_response = await socratic_service.generate_socratic_response(
            config.topic,
            messages,
            0  # understanding_level - will be calculated
        )

        # Add AI response to messages array for complete conversation context in evaluation
        messages.append({"role": "assistant", "content": socratic_response})

        # Store AI response in database
        message_id = None
        try:
            print(f"💬 Saving AI message for student {request.student_id}: {socratic_response[:50]}...")

            result = await storage_service.save_message(
                session_id=session_id,
                student_id=request.student_id,
                content=socratic_response,
                message_type="assistant"
            )
            print(f"✅ AI message saved successfully: {result}")

            # Get the message record ID for score record (one per student)
            try:
                from app.models.database_models import Message
                from app.core.database import AsyncSessionLocal
                from sqlalchemy import select

                async with AsyncSessionLocal() as db_session:
                    stmt = select(Message.id).where(
                        Message.student_id == request.student_id,
                        Message.session_id == session_id
                    )
                    result = await db_session.execute(stmt)
                    message_id = result.scalar_one_or_none()
                    print(f"📝 Found message record ID for scoring: {message_id}")
            except Exception as msg_id_error:
                print(f"⚠️ Could not retrieve message ID: {msg_id_error}")
                message_id = None

        except Exception as e:
            print(f"❌ Error saving AI message: {e}")
            import traceback
            traceback.print_exc()

        # Evaluate understanding using the new message and AI response
        evaluation_result = await assessment_service.evaluate_socratic_dimensions(
            config.topic,
            request.message,
            socratic_response,
            messages,
            config.difficulty
        )

        understanding_score = evaluation_result["overall_score"]
        is_completed = evaluation_result["is_completed"]

        # Record score in database
        if message_id:
            try:
                await storage_service.save_score(
                    message_id=message_id,
                    student_id=request.student_id,
                    session_id=session_id,
                    overall_score=understanding_score,
                    dimensions=evaluation_result["dimensions"],
                    evaluation_data={
                        "insights": evaluation_result.get("insights", []),
                        "growth_indicators": evaluation_result.get("growth_indicators", []),
                        "next_focus": evaluation_result.get("next_focus", [])
                    },
                    is_completed=is_completed
                )
                print(f"✅ Score recorded for student {request.student_id}: {understanding_score}")
            except Exception as e:
                print(f"Warning: Could not save score to database: {e}")

        # Update student progress in session service
        # Note: Message is already saved above, no duplicate save needed
        try:
            await session_service.update_student_progress(
                session_id,
                request.student_id,
                understanding_score,
                evaluation_result["dimensions"],
                is_completed,
                ""  # Message already saved separately above
            )
        except Exception as e:
            print(f"Warning: Could not update student progress: {e}")

        return SessionChatResponse(
            socratic_response=socratic_response,
            understanding_score=understanding_score,
            is_completed=is_completed,
            dimensions=evaluation_result["dimensions"],
            insights=evaluation_result["insights"],
            growth_indicators=evaluation_result["growth_indicators"],
            next_focus=evaluation_result["next_focus"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teacher/sessions/{session_id}/validate")
async def validate_session(session_id: str, request: Request):
    """Validate if session exists and is accessible by teacher"""
    try:
        session_service = get_session_service()
        storage_service = get_storage_service()

        # Generate teacher fingerprint
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # Check if session exists in database
        db_session = await storage_service.get_session_by_id(session_id)
        if not db_session:
            return {"valid": False, "session": None}

        # Check if session belongs to this teacher
        if db_session.teacher.fingerprint != teacher_fingerprint:
            return {"valid": False, "session": None}

        # Convert to dict for JSON serialization
        session_copy = {
            'id': db_session.id,
            'teacher_fingerprint': db_session.teacher.fingerprint,
            'config': {
                'title': db_session.title,
                'topic': db_session.topic,
                'description': db_session.description,
                'difficulty': db_session.difficulty,
                'show_score': db_session.show_score,
                'time_limit': db_session.time_limit,
                'max_students': db_session.max_students
            },
            'status': db_session.status,
            'created_at': db_session.created_at.isoformat(),
            'expires_at': db_session.expires_at.isoformat()
        }
        for field in ['created_at', 'expires_at', 'last_activity', 'ended_at']:
            if field in session_copy and hasattr(session_copy[field], 'isoformat'):
                session_copy[field] = session_copy[field].isoformat()

        return {
            "valid": True,
            "session": {
                "id": session_id,
                "config": session_copy['config'],
                "status": session_copy['status'],
                "created_at": session_copy['created_at'],
                "expires_at": session_copy['expires_at']
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teacher/sessions/{session_id}/archive")
async def archive_session(session_id: str, request: Request):
    """Soft archive a session (doesn't delete, but marks as inactive)"""
    try:
        session_service = get_session_service()
        storage_service = get_storage_service()

        # Generate teacher fingerprint
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # Check if session exists in database and belongs to teacher
        db_session = await storage_service.get_session_by_id(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        if db_session.teacher.fingerprint != teacher_fingerprint:
            raise HTTPException(status_code=403, detail="Not authorized to archive this session")

        # Mark session as deleted (soft delete - data preserved)
        success = await session_service.delete_session(session_id, teacher_fingerprint)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to archive session")

        return {"success": True, "message": "Session archived successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teacher/storage/stats")
async def get_storage_stats():
    """Get storage statistics"""
    try:
        storage_service = get_storage_service()
        stats = await storage_service.get_storage_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teacher/sessions/{session_id}/scores")
async def get_session_scores(session_id: str, request: Request):
    """Get all score records for a session"""
    try:
        session_service = get_session_service()
        storage_service = session_service.storage_service

        # Validate teacher access
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))
        db_session = await storage_service.get_session_by_id(session_id)

        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        if db_session.teacher.fingerprint != teacher_fingerprint:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get scores from database if available
        scores = await storage_service.get_session_scores(session_id)
        return {"scores": scores}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teacher/sessions/{session_id}/students/{student_id}/scores")
async def get_student_scores(session_id: str, student_id: str, request: Request):
    """Get all score records for a specific student"""
    try:
        session_service = get_session_service()
        storage_service = session_service.storage_service

        # Validate teacher access
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))
        db_session = await storage_service.get_session_by_id(session_id)

        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        if db_session.teacher.fingerprint != teacher_fingerprint:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get scores from database
        scores = await storage_service.get_student_scores(session_id, student_id)
        return {"scores": scores}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history/{student_id}")
async def get_student_chat_history(session_id: str, student_id: str):
    """Get chat history for a specific student (public endpoint for student access)"""
    try:
        session_service = get_session_service()
        storage_service = get_storage_service()

        # Verify session exists in database
        db_session = await storage_service.get_session_by_id(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify student is part of this session
        db_student = await storage_service.get_student_by_id(student_id)
        if not db_student or db_student.session_id != session_id:
            raise HTTPException(status_code=403, detail="Student not authorized for this session")

        # Get chat history from database
        try:
            messages = await storage_service.get_student_messages(session_id, student_id)
            return {"messages": messages}
        except Exception as e:
            print(f"Warning: Could not load message history: {e}")
            return {"messages": []}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))