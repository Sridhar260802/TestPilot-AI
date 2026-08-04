from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch

from datetime import datetime
import json
import re



# ===============================
# Helper Functions
# ===============================


def clean_issue_text(issue):

    """
    Remove temp file path from analyzer output
    """

    if ":" in issue:

        parts = issue.split(":", 3)

        if len(parts) >= 4:
            return parts[3].strip()


    return issue



def get_grade(score):

    if score >= 90:
        return "A+"

    elif score >= 80:
        return "A"

    elif score >= 70:
        return "B"

    elif score >= 60:
        return "C"

    else:
        return "D"



def create_styles():

    styles = getSampleStyleSheet()


    return {

        "title":
        ParagraphStyle(
            "title",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=22,
            textColor=colors.HexColor("#1F4E79")
        ),


        "heading":
        ParagraphStyle(
            "heading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#1F4E79")
        ),


        "normal":
        ParagraphStyle(
            "normal",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14
        )

    }





# ===============================
# PDF Generator
# ===============================


def generate_code_pdf(
    data,
    filename="code_analysis_report.pdf"
):


    doc = SimpleDocTemplate(
        filename
    )


    styles = create_styles()


    title = styles["title"]

    heading = styles["heading"]

    normal = styles["normal"]



    story = []



    # ---------------------------
    # Load Data
    # ---------------------------


    analysis = data.get(
        "analysis",
        {}
    )


    security = data.get(
        "security_analysis",
        {}
    )



    if isinstance(
        analysis,
        str
    ):

        analysis = json.loads(
            analysis
        )



    if isinstance(
        security,
        str
    ):

        security = json.loads(
            security
        )



    score = analysis.get(
        "score",
        0
    )


    security_score = security.get(
        "score",
        0
    )




    # ---------------------------
    # Header
    # ---------------------------


    header = Table(

        [

            [

                Paragraph(

                    "<b>TESTPILOT AI</b><br/>"
                    "Code Analysis Report",

                    title

                )

            ]

        ],

        colWidths=[
            450
        ]

    )


    header.setStyle(

        TableStyle(

            [

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,-1),
                    colors.HexColor("#EAF2F8")
                ),


                (
                    "BOX",
                    (0,0),
                    (-1,-1),
                    1,
                    colors.HexColor("#1F4E79")
                ),


                (
                    "ALIGN",
                    (0,0),
                    (-1,-1),
                    "CENTER"
                )

            ]

        )

    )



    story.append(
        header
    )


    story.append(
        Spacer(
            1,
            0.3*inch
        )
    )




    # ---------------------------
    # File Details
    # ---------------------------


    story.append(

        Paragraph(

            f"""
            <b>File Name :</b> {data.get('filename','')}<br/>
            <b>Language :</b> {data.get('language','')}<br/>
            <b>Generated :</b>
            {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
            """,

            normal

        )

    )



    story.append(
        Spacer(
            1,
            0.3*inch
        )
    )




    # ---------------------------
    # Score Dashboard
    # ---------------------------


    score_table = Table(

        [

            [

                "Code Quality",

                "Security",

                "Grade"

            ],


            [

                f"{score}/100",

                f"{security_score}/100",

                get_grade(score)

            ]

        ],

        colWidths=[
            150,
            150,
            150
        ]

    )



    score_table.setStyle(

        TableStyle(

            [

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,0),
                    colors.HexColor("#1F4E79")
                ),


                (
                    "TEXTCOLOR",
                    (0,0),
                    (-1,0),
                    colors.white
                ),


                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    1,
                    colors.grey
                ),


                (
                    "ALIGN",
                    (0,0),
                    (-1,-1),
                    "CENTER"
                )

            ]

        )

    )



    story.append(
        score_table
    )


    story.append(
        Spacer(
            1,
            0.4*inch
        )
    )
        # ===========================
    # Detected Issues
    # ===========================


    story.append(
        Paragraph(
            "Detected Code Issues",
            heading
        )
    )


    issues = analysis.get(
        "issues",
        []
    )


    if isinstance(
        issues,
        str
    ):

        try:
            issues = json.loads(
                issues
            )

        except:

            issues = [
                issues
            ]



    if not issues:


        story.append(

            Paragraph(
                "No issues detected.",
                normal
            )

        )


    else:


        issue_table = [

            [
                "#",
                "Issue Description"
            ]

        ]



        for index, issue in enumerate(
            issues,
            start=1
        ):


            cleaned = clean_issue_text(
                issue
            )


            issue_table.append(

                [

                    str(index),

                    cleaned

                ]

            )




        issue_tbl = Table(

            issue_table,

            colWidths=[
                40,
                380
            ]

        )



        issue_tbl.setStyle(

            TableStyle(

                [

                    (
                        "BACKGROUND",
                        (0,0),
                        (-1,0),
                        colors.HexColor("#1F4E79")
                    ),


                    (
                        "TEXTCOLOR",
                        (0,0),
                        (-1,0),
                        colors.white
                    ),


                    (
                        "GRID",
                        (0,0),
                        (-1,-1),
                        0.5,
                        colors.grey
                    ),


                    (
                        "VALIGN",
                        (0,0),
                        (-1,-1),
                        "TOP"
                    )

                ]

            )

        )



        story.append(
            issue_tbl
        )



    story.append(

        Spacer(
            1,
            0.35*inch
        )

    )





    # ===========================
    # Security Analysis
    # ===========================


    story.append(

        Paragraph(
            "Security Analysis",
            heading
        )

    )



    security_issues = security.get(
        "issues",
        []
    )



    if not security_issues:


        story.append(

            Paragraph(
                "No security issues detected.",
                normal
            )

        )


    else:


        for item in security_issues:


            story.append(

                Paragraph(
                    f"• {item}",
                    normal
                )

            )



    story.append(

        Spacer(
            1,
            0.35*inch
        )

    )





    # ===========================
    # Severity Summary
    # ===========================


    story.append(

        Paragraph(
            "Severity Summary",
            heading
        )

    )



    severity = data.get(
        "severity",
        {}
    )



    if isinstance(
        severity,
        str
    ):

        try:

            severity = json.loads(
                severity
            )

        except:

            severity = {}




    severity_table = [

        [
            "Level",
            "Count"
        ],


        [
            "Critical",
            severity.get(
                "critical",
                0
            )
        ],


        [
            "High",
            severity.get(
                "high",
                0
            )
        ],


        [
            "Medium",
            severity.get(
                "medium",
                0
            )
        ],


        [
            "Low",
            severity.get(
                "low",
                0
            )
        ]

    ]




    sev_table = Table(

        severity_table,

        colWidths=[
            200,
            100
        ]

    )



    sev_table.setStyle(

        TableStyle(

            [

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,0),
                    colors.HexColor("#1F4E79")
                ),


                (
                    "TEXTCOLOR",
                    (0,0),
                    (-1,0),
                    colors.white
                ),


                (
                    "GRID",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.grey
                ),


                (
                    "ALIGN",
                    (1,1),
                    (-1,-1),
                    "CENTER"
                )

            ]

        )

    )


    story.append(
        sev_table
    )



    story.append(

        Spacer(
            1,
            0.35*inch
        )

    )
        # ===========================
    # AI Suggestions
    # ===========================


    story.append(

        Paragraph(
            "AI Code Review Suggestions",
            heading
        )

    )



    ai = data.get(
        "ai_suggestions",
        ""
    )



    if isinstance(ai, dict):

        ai_json = ai


    else:

        try:

            ai = str(ai)

            ai = re.sub(
                r"```json|```",
                "",
                ai
            ).strip()


            ai_json = json.loads(
                ai
            )


        except:


            ai_json = {}





    # Handle double encoded JSON

    if isinstance(ai_json, str):

        try:

            ai_json = json.loads(ai_json)

        except:

            ai_json = {
                "AI Review": ai_json
            }



    if ai_json:


        for key, value in ai_json.items():


            story.append(

                Paragraph(
                    f"<b>{key}</b>",
                    normal
                )

            )



            if isinstance(
                value,
                list
            ):


                for index, item in enumerate(
                    value,
                    start=1
                ):


                    story.append(

                        Paragraph(

                            f"{index}. {item}",

                            normal

                        )

                    )



            else:


                story.append(

                    Paragraph(

                        str(value),

                        normal

                    )

                )



            story.append(

                Spacer(
                    1,
                    0.12*inch
                )

            )



    else:


        story.append(

            Paragraph(

                "No AI suggestions available.",

                normal

            )

        )





    story.append(

        Spacer(
            1,
            0.4*inch
        )

    )





    # ===========================
    # Developer Improvement Summary
    # ===========================


    story.append(

        Paragraph(
            "Recommended Improvements",
            heading
        )

    )


    improvements = [

        "Fix code quality issues reported by analyzer.",

        "Remove unused imports and variables.",

        "Add proper documentation and function docstrings.",

        "Improve security by removing hardcoded credentials.",

        "Follow coding standards and best practices."

    ]



    for index, item in enumerate(
        improvements,
        start=1
    ):


        story.append(

            Paragraph(

                f"{index}. {item}",

                normal

            )

        )




    story.append(

        Spacer(
            1,
            0.5*inch
        )

    )





    # ===========================
    # Footer
    # ===========================


    footer = Table(

        [

            [

                "Generated by TestPilot AI"

            ]

        ],

        colWidths=[
            420
        ]

    )



    footer.setStyle(

        TableStyle(

            [

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,-1),
                    colors.HexColor("#1F4E79")
                ),


                (
                    "TEXTCOLOR",
                    (0,0),
                    (-1,-1),
                    colors.white
                ),


                (
                    "ALIGN",
                    (0,0),
                    (-1,-1),
                    "CENTER"
                ),


                (
                    "TOPPADDING",
                    (0,0),
                    (-1,-1),
                    10
                ),


                (
                    "BOTTOMPADDING",
                    (0,0),
                    (-1,-1),
                    10
                )

            ]

        )

    )



    story.append(
        footer
    )




    # Build PDF

    doc.build(
        story
    )


    return filename