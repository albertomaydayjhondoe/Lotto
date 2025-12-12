"""
Curator AutoMailer — Email Builder STUB

Generates personalized curator emails.
STUB MODE: Returns mock email content.
"""

from typing import Dict, Any
from datetime import datetime


class EmailBuilderStub:
    """
    STUB: Builds personalized emails for curator outreach.
    
    In LIVE mode, this would use:
    - GPT-4/GPT-5 for personalization
    - A&R insights from Music Engine
    - Curator history and preferences
    - Success pattern analysis
    
    Phase 3: Returns mock templated emails.
    """
    
    def __init__(self):
        self.stub_mode = True
        
    def build_pre_release_email(
        self,
        curator_name: str,
        playlist_name: str,
        track_info: Dict[str, Any],
        a_and_r_insights: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        STUB: Build pre-release pitch email.
        
        Args:
            curator_name: Curator's name
            playlist_name: Playlist name
            track_info: Track metadata
            a_and_r_insights: A&R analysis data
            
        Returns:
            Dict with subject, body, and metadata
        """
        artist = track_info.get("artist", "Artist Name")
        title = track_info.get("title", "Track Title")
        genre = track_info.get("genre", "Electronic")
        mood = track_info.get("mood", "Atmospheric")
        release_date = track_info.get("release_date", "TBD")
        
        subject = f"Pre-Release: {artist} - {title} [{genre}] for {playlist_name}"
        
        body = f"""Hi {curator_name},

I hope this email finds you well. I'm reaching out with an exclusive pre-release track that I believe would be a perfect fit for {playlist_name}.

📀 Track: {title}
🎵 Artist: {artist}
🎶 Genre: {genre}
🌊 Vibe: {mood}
📅 Release Date: {release_date}

This track has been carefully crafted with your playlist's aesthetic in mind. {self._generate_a_and_r_highlight(a_and_r_insights)}

I'm offering you exclusive early access before the official release. Would you be interested in reviewing this for consideration?

I can provide:
✓ High-quality pre-release audio
✓ Press materials and artist bio
✓ Pre-save link for your audience

Looking forward to hearing your thoughts!

Best regards,
Stakazo A&R Team

---
STUB MODE - Template generated automatically
"""
        
        return {
            "subject": subject,
            "body": body,
            "email_type": "pre_release_pitch",
            "personalization_level": "medium",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def build_post_release_email(
        self,
        curator_name: str,
        playlist_name: str,
        track_info: Dict[str, Any],
        spotify_url: str,
        compatibility_score: float = None
    ) -> Dict[str, str]:
        """
        STUB: Build post-release pitch email.
        
        Args:
            curator_name: Curator's name
            playlist_name: Playlist name
            track_info: Track metadata
            spotify_url: Spotify track URL
            compatibility_score: Playlist fit score
            
        Returns:
            Dict with subject, body, and metadata
        """
        artist = track_info.get("artist", "Artist Name")
        title = track_info.get("title", "Track Title")
        genre = track_info.get("genre", "Electronic")
        bpm = track_info.get("bpm", 124)
        
        subject = f"New Release: {artist} - {title} for {playlist_name}"
        
        compatibility_note = ""
        if compatibility_score and compatibility_score >= 0.80:
            compatibility_note = f"\n🎯 AI Compatibility Score: {compatibility_score:.0%} - Strong Match!"
        
        body = f"""Hi {curator_name},

I wanted to share a fresh release that aligns perfectly with the vibe of {playlist_name}.
{compatibility_note}

📀 {title} by {artist}
🎶 Genre: {genre} | BPM: {bpm}
🔗 Spotify: {spotify_url}

This track has been generating buzz in the {genre} community, and I believe it would resonate strongly with your audience.

Key highlights:
✓ Professional production quality
✓ Genre: {genre}
✓ Perfect for {playlist_name}'s aesthetic
✓ Growing artist momentum

Would love to hear your feedback!

Best,
Stakazo Playlist Team

---
STUB MODE - Auto-generated pitch
"""
        
        return {
            "subject": subject,
            "body": body,
            "email_type": "post_release_pitch",
            "personalization_level": "medium",
            "compatibility_score": compatibility_score,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def build_follow_up_email(
        self,
        curator_name: str,
        original_track_info: Dict[str, Any],
        days_since_initial: int = 7
    ) -> Dict[str, str]:
        """
        STUB: Build follow-up email.
        
        Args:
            curator_name: Curator's name
            original_track_info: Original track info
            days_since_initial: Days since first email
            
        Returns:
            Dict with subject, body, and metadata
        """
        artist = original_track_info.get("artist", "Artist Name")
        title = original_track_info.get("title", "Track Title")
        
        subject = f"Following up: {artist} - {title}"
        
        body = f"""Hi {curator_name},

I wanted to gently follow up on the track I shared {days_since_initial} days ago:

{artist} - {title}

I understand you receive many submissions, so no worries if this one isn't the right fit. I'd appreciate any feedback if you have a moment.

If you need any additional information or materials, I'm happy to provide them.

Thanks for your time!

Best,
Stakazo Team

---
STUB MODE - Auto-generated follow-up
"""
        
        return {
            "subject": subject,
            "body": body,
            "email_type": "follow_up",
            "personalization_level": "low",
            "days_since_initial": days_since_initial,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def build_thank_you_email(
        self,
        curator_name: str,
        playlist_name: str,
        track_title: str
    ) -> Dict[str, str]:
        """
        STUB: Build thank you email after playlist add.
        
        Args:
            curator_name: Curator's name
            playlist_name: Playlist name
            track_title: Track title
            
        Returns:
            Dict with subject, body, and metadata
        """
        subject = f"Thank you for adding {track_title} to {playlist_name}!"
        
        body = f"""Hi {curator_name},

Thank you so much for adding {track_title} to {playlist_name}! We truly appreciate your support and belief in the music.

We're excited to see how your audience responds to it. If there's anything we can do to support the playlist or if you'd like early access to future releases, please let us know.

Looking forward to continuing this relationship!

Gratefully,
Stakazo Team

---
STUB MODE - Auto-generated thank you
"""
        
        return {
            "subject": subject,
            "body": body,
            "email_type": "thank_you",
            "personalization_level": "medium",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_a_and_r_highlight(
        self,
        a_and_r_insights: Dict[str, Any]
    ) -> str:
        """Generate A&R highlight text"""
        if not a_and_r_insights:
            return "Our A&R team has identified this as a standout release."
        
        score = a_and_r_insights.get("a_and_r_score", 7.5)
        
        if score >= 8.5:
            return "Our A&R team rates this as an exceptional release with strong commercial potential."
        elif score >= 7.5:
            return "This track has received strong marks from our A&R analysis for quality and appeal."
        else:
            return "Our team believes this track shows great promise for playlist placement."
