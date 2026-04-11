import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from typing import List
from models.video import VideoResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Register a font that supports Hindi characters
def register_fonts():
    # Bundled fonts in the repository take precedence
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bundled_regular = os.path.join(base_dir, "fonts", "NotoSansDevanagari-Regular.ttf")
    bundled_bold = os.path.join(base_dir, "fonts", "NotoSansDevanagari-Bold.ttf")

    # Potential paths for various environments
    font_paths = [
        bundled_regular,
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    font_bold_paths = [
        bundled_bold,
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    registered_name = 'Helvetica'
    registered_bold_name = 'Helvetica-Bold'

    try:
        # Try to find and register the main font
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('CustomFont', path))
                registered_name = 'CustomFont'
                logger.info(f"Registered main font from {path}")
                break

        # Try to find and register the bold font
        for path in font_bold_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('CustomFont-Bold', path))
                registered_bold_name = 'CustomFont-Bold'
                logger.info(f"Registered bold font from {path}")
                break

        if registered_name == 'Helvetica':
            logger.warning("No suitable TrueType font found for Hindi support. Using Helvetica.")

    except Exception as e:
        logger.error(f"Error registering font: {e}")

    return registered_name, registered_bold_name

DEFAULT_FONT, DEFAULT_FONT_BOLD = register_fonts()

class ExportService:
    
    def export_to_csv(self, videos: List[VideoResponse], search_params: dict) -> str:
        """
        Export video data to CSV format with UTF-8 BOM for Excel compatibility
        """
        try:
            output = io.StringIO()
            # Add UTF-8 BOM
            output.write('\ufeff')
            writer = csv.writer(output)
            
            # Write header - matching the "Video Details" table in the image
            writer.writerow([
                'Title',
                'Channel',
                'Views',
                'Likes',
                'Comments',
                'Sentiment'
            ])
            
            # Write data
            for video in videos:
                # Use Excel formula for hyperlinks in CSV
                # Clean title to avoid formula breaking (Excel allows up to 255 chars in HYPERLINK text sometimes,
                # but let's just make sure quotes are handled)
                clean_title = video.title.replace('"', '""')
                hyperlink_formula = f'=HYPERLINK("{video.url}","{clean_title}")'

                writer.writerow([
                    hyperlink_formula,
                    video.channel,
                    video.views,
                    video.likes,
                    video.comments,
                    video.sentiment
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            return csv_content
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def export_to_pdf(self, videos: List[VideoResponse], search_params: dict) -> bytes:
        """
        Export video data to PDF format with charts and professional formatting
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=DEFAULT_FONT_BOLD,
                fontSize=20,
                spaceAfter=30,
                textColor=colors.darkred
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=DEFAULT_FONT_BOLD,
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("YouTube Trends Analysis Report", title_style))
            story.append(Spacer(1, 20))
            
            # Search parameters
            story.append(Paragraph("Search Parameters", heading_style))
            param_data = [
                ['Keywords:', search_params.get('keywords', 'N/A')],
                ['Date Range:', f"{search_params.get('startDate', 'N/A')} to {search_params.get('endDate', 'N/A')}"],
                ['Region:', search_params.get('region', 'N/A')],
                ['Total Videos:', str(len(videos))],
                ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            ]
            
            param_table = Table(param_data, colWidths=[2*inch, 4*inch])
            param_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(param_table)
            story.append(Spacer(1, 30))
            
            # Summary statistics
            story.append(Paragraph("Analytics Summary", heading_style))
            
            total_views = sum(video.views for video in videos)
            total_likes = sum(video.likes for video in videos)
            total_comments = sum(video.comments for video in videos)
            
            # Sentiment analysis
            sentiment_counts = {}
            for video in videos:
                sentiment_counts[video.sentiment] = sentiment_counts.get(video.sentiment, 0) + 1
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Views', f"{total_views:,}"],
                ['Total Likes', f"{total_likes:,}"],
                ['Total Comments', f"{total_comments:,}"],
                ['Average Views per Video', f"{total_views // len(videos) if videos else 0:,}"],
                ['Positive Sentiment', f"{sentiment_counts.get('Positive', 0)} videos"],
                ['Negative Sentiment', f"{sentiment_counts.get('Negative', 0)} videos"],
                ['Neutral Sentiment', f"{sentiment_counts.get('Neutral', 0)} videos"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Video details table
            story.append(Paragraph("Video Details", heading_style))
            
            # Style for wrapped text in table cells
            cell_style = ParagraphStyle(
                'TableCell',
                fontName=DEFAULT_FONT,
                fontSize=8,
                leading=10
            )

            # Prepare table data
            table_data = [[
                Paragraph('<b>Title</b>', cell_style),
                Paragraph('<b>Channel</b>', cell_style),
                Paragraph('<b>Views</b>', cell_style),
                Paragraph('<b>Likes</b>', cell_style),
                Paragraph('<b>Comments</b>', cell_style),
                Paragraph('<b>Sentiment</b>', cell_style)
            ]]
            
            for video in videos[:200]:  # Limit to first 200 videos for PDF
                title_with_link = f'<a href="{video.url}" color="blue">{video.title}</a>'
                table_data.append([
                    Paragraph(title_with_link, cell_style),
                    Paragraph(video.channel, cell_style),
                    f"{video.views:,}",
                    f"{video.likes:,}",
                    f"{video.comments:,}",
                    video.sentiment
                ])
            
            # Create table
            video_table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch], repeatRows=1)
            video_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 1), (-1, -1), DEFAULT_FONT),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
            ]))
            
            story.append(video_table)
            
            # Add note if more videos exist
            if len(videos) > 200:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Note: Showing first 200 videos out of {len(videos)} total results.", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise