import csv
import io
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import requests
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
    
    def _format_count(self, count: int) -> str:
        """Formats numbers like 427300 to 427.3K"""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        if count >= 1_000:
            val = count / 1_000
            if val >= 100:
                return f"{val:.1f}K"
            return f"{val:.1f}K" # Matching dashboard style
        return str(count)

    def _get_image(self, url: str):
        """Fetch image from URL and return a ReportLab Image object"""
        try:
            if not url:
                return None
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                img_data = io.BytesIO(resp.content)
                img = RLImage(img_data)
                # Resize thumbnail - standard YT is 120x90 or 480x360.
                # We want it small for the table.
                img.drawHeight = 0.6 * inch
                img.drawWidth = 0.8 * inch
                return img
        except Exception as e:
            logger.error(f"Error fetching thumbnail {url}: {e}")
        return None

    def export_to_csv(self, videos: List[VideoResponse], search_params: dict) -> str:
        """
        Export video data to CSV format with UTF-8 BOM for Excel compatibility
        """
        try:
            output = io.StringIO()
            # Add UTF-8 BOM
            output.write('\ufeff')
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Timestamp',
                'Title',
                'Channel',
                'Views',
                'Likes',
                'Comments',
                'Sentiment',
                'Description',
                'URL',
                'Thumbnail URL'
            ])
            
            # Write data
            for video in videos:
                clean_title = video.title.replace('"', '""')
                hyperlink_formula = f'=HYPERLINK("{video.url}","{clean_title}")'

                writer.writerow([
                    video.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    hyperlink_formula,
                    video.channel,
                    video.views,
                    video.likes,
                    video.comments,
                    video.sentiment,
                    video.description,
                    video.url,
                    video.thumbnail
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            return csv_content
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def export_to_pdf(self, videos: List[VideoResponse], search_params: dict) -> bytes:
        """
        Export video data to PDF format matching the dashboard layout
        """
        try:
            buffer = io.BytesIO()
            # Use Landscape for better table fit
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                  rightMargin=30, leftMargin=30,
                                  topMargin=30, bottomMargin=30)
            
            styles = getSampleStyleSheet()

            # Custom Styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=DEFAULT_FONT_BOLD,
                fontSize=18,
                spaceAfter=20,
                textColor=colors.darkblue
            )
            
            header_style = ParagraphStyle(
                'TableHeader',
                fontName=DEFAULT_FONT_BOLD,
                fontSize=10,
                textColor=colors.black,
                alignment=TA_CENTER
            )

            timestamp_style = ParagraphStyle(
                'TimestampStyle',
                fontName=DEFAULT_FONT,
                fontSize=9,
                alignment=TA_CENTER
            )

            # Video Content Styles
            v_title_style = ParagraphStyle(
                'VideoTitle',
                fontName=DEFAULT_FONT_BOLD,
                fontSize=10,
                leading=12,
                textColor=colors.black
            )
            v_channel_style = ParagraphStyle(
                'VideoChannel',
                fontName=DEFAULT_FONT,
                fontSize=9,
                leading=11,
                textColor=colors.grey
            )
            v_desc_style = ParagraphStyle(
                'VideoDesc',
                fontName=DEFAULT_FONT,
                fontSize=8,
                leading=10,
                textColor=colors.darkgrey
            )

            # Metrics Styles
            views_style = ParagraphStyle('ViewsStyle', fontName=DEFAULT_FONT_BOLD, fontSize=10, textColor=colors.red, alignment=TA_CENTER)
            likes_style = ParagraphStyle('LikesStyle', fontName=DEFAULT_FONT_BOLD, fontSize=10, textColor=colors.green, alignment=TA_CENTER)
            comments_style = ParagraphStyle('CommentsStyle', fontName=DEFAULT_FONT_BOLD, fontSize=10, textColor=colors.blue, alignment=TA_CENTER)

            story = []

            story.append(Paragraph(f"YouTube Analysis Report - {search_params.get('keywords', 'General')}", title_style))

            # Prepare Table Data
            # Header
            table_data = [[
                Paragraph('Timestamp', header_style),
                Paragraph('Video Content', header_style),
                Paragraph('Views', header_style),
                Paragraph('Likes', header_style),
                Paragraph('Comments', header_style),
                Paragraph('Sentiment', header_style)
            ]]
            
            for video in videos[:200]:
                # 1. Timestamp Column
                # Match image: 13 Apr 2026, 03:11 pm
                ts_date = video.timestamp.strftime('%d %b %Y,')
                ts_time = video.timestamp.strftime('%I:%M %p').lower()
                ts_str = f"{ts_date}\n{ts_time}"
                ts_para = Paragraph(ts_str, timestamp_style)

                # 2. Video Content Column (Nested Table: [Thumbnail | Text])
                thumb = self._get_image(video.thumbnail)
                if not thumb:
                    # Fallback if image fails
                    thumb = Paragraph("", v_desc_style)

                content_text = [
                    Paragraph(f'<a href="{video.url}" color="black"><b>{video.title}</b></a>', v_title_style),
                    Paragraph(video.channel, v_channel_style),
                    Paragraph(video.description[:150] + "..." if len(video.description) > 150 else video.description, v_desc_style)
                ]

                # Nested table for the "Video Content" cell to put thumbnail next to text
                inner_table = Table([[thumb, content_text]], colWidths=[0.9*inch, 5.0*inch])
                inner_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))

                # 3, 4, 5. Metrics
                v_views = Paragraph(self._format_count(video.views), views_style)
                v_likes = Paragraph(self._format_count(video.likes), likes_style)
                v_comments = Paragraph(str(video.comments), comments_style)

                # 6. Sentiment Pill
                sent_color = colors.lightgrey
                sent_text_color = colors.black
                if video.sentiment == 'Positive':
                    sent_color = colors.honeydew
                    sent_text_color = colors.green
                elif video.sentiment == 'Negative':
                    sent_color = colors.mistyrose
                    sent_text_color = colors.red

                sent_style = ParagraphStyle(
                    'SentStyle',
                    fontName=DEFAULT_FONT,
                    fontSize=9,
                    alignment=TA_CENTER,
                    textColor=sent_text_color,
                    backColor=sent_color,
                    borderPadding=4,
                    borderRadius=5
                )
                v_sentiment = Paragraph(video.sentiment, sent_style)

                table_data.append([
                    ts_para,
                    inner_table,
                    v_views,
                    v_likes,
                    v_comments,
                    v_sentiment
                ])

            # Main Table
            # Total width for Landscape A4 (11.69in) minus margins (approx 1in total) = ~10.6in
            # Timstamp: 1.0, Video Content: 6.0, Views: 0.8, Likes: 0.8, Comments: 0.8, Sentiment: 1.0 = 10.4
            col_widths = [1.1*inch, 6.0*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.0*inch]
            main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            main_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.lightgrey),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.whitesmoke),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Video content left aligned
            ]))

            story.append(main_table)
            
            if len(videos) > 200:
                story.append(Spacer(1, 15))
                story.append(Paragraph(f"Note: Report limited to top 200 videos. Total results found: {len(videos)}.", styles['Italic']))

            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
