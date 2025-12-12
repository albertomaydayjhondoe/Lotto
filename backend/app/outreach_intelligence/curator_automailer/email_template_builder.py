"""
Curator AutoMailer — Email Template Builder

Builds professional, personalized email templates for curator outreach.
Adapts tone and content based on curator type, playlist category, and artist brand.

POST-RELEASE ONLY: Auto-sends after track is released.
PRE-RELEASE: Templates generated but require manual review.

STUB MODE: Returns mock templates.
"""

from typing import Dict, Any, List
from datetime import datetime


class EmailTemplateBuilder:
    """
    STUB: Builds email templates for curator outreach.
    
    In LIVE mode:
    - Uses GPT-5 for personalization
    - A/B tests subject lines
    - Tracks open/click rates per template style
    - Learns from successful outreach
    
    Phase 4: Returns mock templates.
    """
    
    def __init__(self):
        self.stub_mode = True
        
    def build_initial_pitch(
        self,
        curator_info: Dict[str, Any],
        track_info: Dict[str, Any],
        artist_info: Dict[str, Any],
        reasoning: str
    ) -> Dict[str, Any]:
        """
        STUB: Build initial pitch email.
        
        POST-RELEASE: Auto-sent to independent playlists.
        
        Args:
            curator_info: Curator/playlist details
            track_info: Track information
            artist_info: Artist profile
            reasoning: Why track fits playlist
            
        Returns:
            Email template dict
        """
        curator_name = curator_info.get("name", "Curator")
        playlist_name = curator_info.get("playlist_name", "your playlist")
        track_title = track_info.get("title", "Track")
        artist_name = artist_info.get("name", "Artist")
        spotify_url = track_info.get("spotify_url", "https://open.spotify.com/track/...")
        
        # STUB: Professional template
        subject = f"Track Submission for {playlist_name}: {track_title}"
        
        body = f"""Hi {curator_name},

I hope this message finds you well. I've been following {playlist_name} and really admire your curation style.

I'd love to submit "{track_title}" by {artist_name} for your consideration. {reasoning}

Track Details:
• Genre: {track_info.get('genre', 'Electronic')}
• Mood: {track_info.get('mood', 'Atmospheric')}
• BPM: {track_info.get('bpm', '124')}
• Released: {track_info.get('release_date', 'Recently')}

Listen here: {spotify_url}

I believe this track would resonate with your playlist's audience. Would love to hear your thoughts!

Best regards,
{artist_info.get('contact_name', artist_name)}
{artist_info.get('email', 'artist@example.com')}

--
This is a personalized submission. If you'd prefer not to receive future submissions, please let me know.
"""
        
        return {
            "type": "initial_pitch",
            "to": curator_info.get("email", "curator@example.com"),
            "subject": subject,
            "body": body,
            "track_url": spotify_url,
            "personalization_level": "high",
            "auto_send": True,  # POST-RELEASE
            "priority": curator_info.get("priority", "medium"),
            "stub_note": "STUB MODE - Would send via email API"
        }
    
    def build_follow_up(
        self,
        original_email: Dict[str, Any],
        days_since_sent: int,
        curator_info: Dict[str, Any],
        track_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        STUB: Build follow-up email.
        
        Sent automatically 7 days after initial pitch if no response.
        
        Args:
            original_email: Original email sent
            days_since_sent: Days since original
            curator_info: Curator information
            track_info: Track details
            
        Returns:
            Follow-up email template
        """
        curator_name = curator_info.get("name", "Curator")
        track_title = track_info.get("title", "Track")
        
        subject = f"Re: Track Submission for {curator_info.get('playlist_name', 'your playlist')}"
        
        body = f"""Hi {curator_name},

I wanted to follow up on my submission of "{track_title}" from {days_since_sent} days ago.

I understand you receive many submissions and wanted to check if you had a chance to listen. No pressure at all – just wanted to make sure it didn't get lost in your inbox!

The track is performing well and getting positive feedback. I genuinely think it would be a great fit for your playlist's vibe.

Track link: {track_info.get('spotify_url', 'https://open.spotify.com/track/...')}

Thanks for your time!

Best,
{track_info.get('artist_name', 'Artist')}
"""
        
        return {
            "type": "follow_up",
            "to": curator_info.get("email"),
            "subject": subject,
            "body": body,
            "auto_send": True,
            "max_follow_ups": 1,  # Only one follow-up
            "stub_note": "STUB MODE - Send 7 days after initial pitch"
        }
    
    def build_thank_you(
        self,
        curator_info: Dict[str, Any],
        track_info: Dict[str, Any],
        placement_date: str
    ) -> Dict[str, Any]:
        """
        STUB: Build thank you email after playlist add.
        
        Sent automatically when track is added to playlist.
        
        Args:
            curator_info: Curator details
            track_info: Track information
            placement_date: When track was added
            
        Returns:
            Thank you email template
        """
        curator_name = curator_info.get("name", "Curator")
        playlist_name = curator_info.get("playlist_name", "your playlist")
        track_title = track_info.get("title", "Track")
        
        subject = f"Thank you for adding {track_title} to {playlist_name}!"
        
        body = f"""Hi {curator_name},

Thank you so much for adding "{track_title}" to {playlist_name}!

I really appreciate your support and I'm excited to see how the track resonates with your audience. Your playlist has great taste and reach.

I'll keep you updated on future releases – would love to work with you again.

Thanks again!

Best regards,
{track_info.get('artist_name', 'Artist')}
"""
        
        return {
            "type": "thank_you",
            "to": curator_info.get("email"),
            "subject": subject,
            "body": body,
            "auto_send": True,
            "send_immediately": True,
            "stub_note": "STUB MODE - Trigger on playlist add detection"
        }
    
    def build_re_engagement(
        self,
        curator_info: Dict[str, Any],
        track_info: Dict[str, Any],
        previous_interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        STUB: Build re-engagement email for future releases.
        
        Sent to curators who previously added tracks.
        
        Args:
            curator_info: Curator details
            track_info: New track information
            previous_interactions: History with curator
            
        Returns:
            Re-engagement email template
        """
        curator_name = curator_info.get("name", "Curator")
        playlist_name = curator_info.get("playlist_name", "your playlist")
        track_title = track_info.get("title", "Track")
        
        # Count previous placements
        placements = len([i for i in previous_interactions if i.get("placed", False)])
        
        subject = f"New Release: {track_title}"
        
        if placements > 0:
            body = f"""Hi {curator_name},

Hope you're doing well! You've supported my music by adding {placements} track(s) to {playlist_name} – thank you!

I have a new release that I think you'll love: "{track_title}"

Based on how my previous tracks performed on your playlist, I believe this one will resonate even better with your audience.

Listen here: {track_info.get('spotify_url', 'https://open.spotify.com/track/...')}

Would love your thoughts!

Best,
{track_info.get('artist_name', 'Artist')}
"""
        else:
            body = f"""Hi {curator_name},

I hope you remember me – I reached out a while back about my music for {playlist_name}.

I have a new release: "{track_title}" and I immediately thought of your playlist. The production and vibe are much stronger than my previous work.

Would love if you could give it a listen: {track_info.get('spotify_url', 'https://open.spotify.com/track/...')}

Thanks for considering!

Best,
{track_info.get('artist_name', 'Artist')}
"""
        
        return {
            "type": "re_engagement",
            "to": curator_info.get("email"),
            "subject": subject,
            "body": body,
            "auto_send": True,
            "relationship_level": "warm" if placements > 0 else "cold",
            "stub_note": "STUB MODE - Track curator relationships"
        }
    
    def customize_for_platform(
        self,
        template: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """
        STUB: Customize template for specific platform.
        
        Adjusts messaging based on platform (Spotify, YouTube, Blog, etc.)
        
        Args:
            template: Base email template
            platform: Target platform (spotify, youtube, blog, etc.)
            
        Returns:
            Platform-customized template
        """
        # STUB: Add platform-specific customization
        if platform.lower() == "youtube":
            template["body"] += "\n\nP.S. I'd also love to send you the official music video if you're interested!"
        elif platform.lower() == "blog":
            template["body"] += "\n\nP.S. I have high-res photos and a press kit available if you'd like to feature the track."
        elif platform.lower() == "radio":
            template["body"] += "\n\nP.S. I'm available for interviews or live sessions if that interests you!"
        
        template["platform"] = platform
        template["customized"] = True
        
        return template
