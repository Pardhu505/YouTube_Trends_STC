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
            return f"{val:.1f}K"
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
            output.write('\ufeff')
            writer = csv.writer(output)
            
            writer.writerow([
                'Timestamp',
                'Title',
                'Channel',
                'Views',
                'Likes',
                'Comments',
                'Sentiment',
                'URL',
                'Thumbnail URL',
                'Description'
            ])
            
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
                    video.url,
                    video.thumbnail,
                    video.description
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
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                  rightMargin=30, leftMargin=30,
                                  topMargin=30, bottomMargin=30)
            
            styles = getSampleStyleSheet()

            # Custom Styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=DEFAULT_FONT_BOLD,
                fontSize=20,
                spaceAfter=20,
                textColor=colors.darkblue,
                alignment=TA_LEFT
            )
            
            section_header_style = ParagraphStyle(
                'SectionHeader',
                fontName=DEFAULT_FONT_BOLD,
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10,
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

            story.append(Paragraph("YouTube Trends Analysis Report", title_style))

            # 1. Search Parameters Table
            story.append(Paragraph("Search Parameters", section_header_style))
            param_data = [
                [Paragraph('Keywords:', header_style), search_params.get('keywords', 'N/A')],
                [Paragraph('Date Range:', header_style), f"{search_params.get('startDate', 'N/A')} to {search_params.get('endDate', 'N/A')}"],
                [Paragraph('Total Videos:', header_style), str(len(videos))],
                [Paragraph('Generated:', header_style), datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            ]
            param_table = Table(param_data, colWidths=[2*inch, 4*inch])
            param_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (1, 0), (1, -1), DEFAULT_FONT),
                ('FONTSIZE', (1, 0), (1, -1), 10),
                ('LEFTPADDING', (1, 0), (1, -1), 10),
            ]))
            story.append(param_table)
            story.append(Spacer(1, 15))

            # 2. Analytics Summary Tables
            story.append(Paragraph("Overall Performance Metrics", section_header_style))
            
            total_views = sum(video.views for video in videos)
            total_likes = sum(video.likes for video in videos)
            total_comments = sum(video.comments for video in videos)
            total_engagement = total_likes + total_comments
            avg_views = total_views // len(videos) if videos else 0
            avg_likes = total_likes // len(videos) if videos else 0
            avg_comments = total_comments // len(videos) if videos else 0

            # Performance Table (2 columns, 4 rows)
            perf_data = [
                [Paragraph('Metric', header_style), Paragraph('Total Value', header_style), Paragraph('Average per Video', header_style)],
                ['Views', f"{total_views:,}", f"{avg_views:,}"],
                ['Likes', f"{total_likes:,}", f"{avg_likes:,}"],
                ['Comments', f"{total_comments:,}", f"{avg_comments:,}"],
                ['Total Engagement', f"{total_engagement:,}", 'N/A']
            ]
            perf_table = Table(perf_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
            perf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), DEFAULT_FONT),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ]))
            story.append(perf_table)
            story.append(Spacer(1, 15))

            # Sentiment Table
            story.append(Paragraph("Sentiment Distribution", section_header_style))
            sentiment_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
            for v in videos:
                sentiment_counts[v.sentiment] = sentiment_counts.get(v.sentiment, 0) + 1
            
            total_v = len(videos)
            sent_data = [
                [Paragraph('Sentiment', header_style), Paragraph('Count', header_style), Paragraph('Percentage', header_style)],
                [Paragraph('Positive', ParagraphStyle('Pos', textColor=colors.green, alignment=TA_CENTER, fontName=DEFAULT_FONT_BOLD)), 
                 str(sentiment_counts['Positive']), f"{(sentiment_counts['Positive']/total_v*100):.1f}%" if total_v > 0 else "0%"],
                [Paragraph('Negative', ParagraphStyle('Neg', textColor=colors.red, alignment=TA_CENTER, fontName=DEFAULT_FONT_BOLD)), 
                 str(sentiment_counts['Negative']), f"{(sentiment_counts['Negative']/total_v*100):.1f}%" if total_v > 0 else "0%"],
                [Paragraph('Neutral', ParagraphStyle('Neu', textColor=colors.grey, alignment=TA_CENTER, fontName=DEFAULT_FONT_BOLD)), 
                 str(sentiment_counts['Neutral']), f"{(sentiment_counts['Neutral']/total_v*100):.1f}%" if total_v > 0 else "0%"]
            ]
            
            sent_table = Table(sent_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
            sent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), DEFAULT_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            story.append(sent_table)
            story.append(Spacer(1, 20))

            # 3. Video Details Table
            story.append(Paragraph("Video Details", section_header_style))
            table_data = [[
                Paragraph('Timestamp', header_style),
                Paragraph('Video Content', header_style),
                Paragraph('Views', header_style),
                Paragraph('Likes', header_style),
                Paragraph('Comments', header_style),
                Paragraph('Sentiment', header_style),
                Paragraph('Link', header_style)
            ]]
            
            for video in videos[:200]:
                ts_date = video.timestamp.strftime('%d %b %Y,')
                ts_time = video.timestamp.strftime('%I:%M %p').lower()
                ts_para = Paragraph(f"{ts_date}<br/>{ts_time}", timestamp_style)

                thumb = self._get_image(video.thumbnail)
                if not thumb:
                    thumb = Paragraph("", v_desc_style)

                content_text = [
                    Paragraph(f'<a href="{video.url}" color="blue"><b>{video.title}</b></a>', v_title_style),
                    Paragraph(video.channel, v_channel_style),
                    Paragraph(video.description[:150] + "..." if len(video.description) > 150 else video.description, v_desc_style)
                ]

                inner_table = Table([[thumb, content_text]], colWidths=[0.9*inch, 5.0*inch])
                inner_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))

                v_views = Paragraph(self._format_count(video.views), views_style)
                v_likes = Paragraph(self._format_count(video.likes), likes_style)
                v_comments = Paragraph(str(video.comments), comments_style)

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

                v_link = Paragraph(f'<a href="{video.url}" color="blue">Watch</a>', timestamp_style)

                table_data.append([
                    ts_para,
                    inner_table,
                    v_views,
                    v_likes,
                    v_comments,
                    v_sentiment,
                    v_link
                ])

            col_widths = [1.1*inch, 5.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.0*inch, 0.8*inch]
            main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            main_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.lightgrey),
                ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.whitesmoke),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
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
