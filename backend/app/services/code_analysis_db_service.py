import json

from app.models.code_analysis import CodeAnalysis



def save_code_analysis(
    db,
    filename,
    language,
    analysis,
    severity,
    ai
):

    data = CodeAnalysis(

        filename=filename,

        language=language,

        score=analysis.get(
            "score",
            0
        ),

        issues=json.dumps(
            analysis.get(
                "issues",
                []
            )
        ),

        severity=json.dumps(
            severity
        ),

        ai_suggestions=str(ai)

    )


    db.add(data)

    db.commit()

    db.refresh(data)


    return data


def get_code_analysis_history(db):

    return (
        db.query(CodeAnalysis)
        .order_by(
            CodeAnalysis.created_at.desc()
        )
        .all()
    )