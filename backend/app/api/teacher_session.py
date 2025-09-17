from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from app.models.session_models import (
    SessionCreateRequest, SessionCreateResponse, SessionConfig,
    TeacherSessionsResponse, SessionDetailsResponse, SessionJoinRequest,
    SessionJoinResponse, QRCodeInfo, SessionInfo
)
from app.services.session_service import get_session_service
from app.services.qr_service import get_qr_service
from app.services.socratic_service import SocraticService
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

        # Get base URL from request
        base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost:8001')}"

        # Create session
        session_result = await session_service.create_session(config, teacher_fingerprint, base_url)
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

        # Calculate summary stats
        total_sessions = len(sessions)
        total_students = sum(s.get('live_stats', {}).get('total_joined', 0) for s in sessions)

        # Calculate average score from active sessions
        active_sessions = [s for s in sessions if s['status'] == 'active']
        if active_sessions:
            avg_score = sum(s.get('live_stats', {}).get('average_score', 0) for s in active_sessions) / len(active_sessions)
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
    try:
        session_service = get_session_service()

        # Generate teacher fingerprint
        teacher_fingerprint = session_service.generate_browser_fingerprint(dict(request.headers))

        # Get session details
        session_details = await session_service.get_session_details(session_id, teacher_fingerprint)
        if not session_details:
            raise HTTPException(status_code=404, detail="Session not found")

        session_data = session_details['session']
        students = session_details['students']

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

        # Check if session exists and is active
        session_data = session_service.active_sessions.get(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_data['status'] == 'expired':
            raise HTTPException(status_code=410, detail="Session has expired")

        config = SessionConfig(**session_data['config'])

        return {
            "session": {
                "id": session_id,
                "topic": config.topic,
                "description": config.description,
                "difficulty": config.difficulty,
                "show_score": config.show_score,
                "estimated_time": f"{config.time_limit}분",
                "is_active": session_data['status'] in ['waiting', 'active']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/{session_id}/join", response_model=SessionJoinResponse)
async def join_session(session_id: str, request: SessionJoinRequest):
    """Student joins a session"""
    try:
        session_service = get_session_service()
        socratic_service = get_socratic_service()

        # Join session
        join_result = await session_service.join_session(session_id)
        if not join_result:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        student_id = join_result['student_id']
        session_config = join_result['session_config']

        # Generate initial message
        initial_message = await socratic_service.generate_initial_message(session_config.topic)

        return SessionJoinResponse(
            success=True,
            student_id=student_id,
            session_config=session_config,
            initial_message=initial_message,
            understanding_score=0
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qr/{session_id}.png")
async def download_qr_code(session_id: str):
    """Download QR code image"""
    try:
        session_service = get_session_service()
        qr_service = get_qr_service()

        # Check if session exists
        session_data = session_service.active_sessions.get(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Generate QR code for download (larger size)
        base_url = "https://yourapp.com"  # This should come from config
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