import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from typing import List
from models.video import VideoResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExportService:
    
    def export_to_csv(self, videos: List[VideoResponse], search_params: dict) -> str:
        """
        Export video data to CSV format
        """
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Timestamp',
                'Title',
                'Channel',
                'Description',
                'Views',
                'Likes',
                'Comments',
                'Sentiment',
                'URL'
            ])
            
            # Write data
            for video in videos:
                writer.writerow([
                    video.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    video.title,
                    video.channel,
                    video.description,
                    video.views,
                    video.likes,
                    video.comments,
                    video.sentiment,
                    video.url
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
                fontSize=20,
                spaceAfter=30,
                textColor=colors.darkred
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
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
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
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
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Video details table
            story.append(Paragraph("Video Details", heading_style))
            
            # Prepare table data
            table_data = [['Title', 'Channel', 'Views', 'Likes', 'Comments', 'Sentiment']]
            
            for video in videos[:20]:  # Limit to first 20 videos for PDF
                table_data.append([
                    video.title[:40] + '...' if len(video.title) > 40 else video.title,
                    video.channel[:20] + '...' if len(video.channel) > 20 else video.channel,
                    f"{video.views:,}",
                    f"{video.likes:,}",
                    f"{video.comments:,}",
                    video.sentiment
                ])
            
            # Create table
            video_table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
            video_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
            ]))
            
            story.append(video_table)
            
            # Add note if more videos exist
            if len(videos) > 20:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Note: Showing first 20 videos out of {len(videos)} total results.", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise