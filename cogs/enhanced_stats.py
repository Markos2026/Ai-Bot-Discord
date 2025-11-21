import discord
from discord.ext import commands
from discord import app_commands
import io
from datetime import datetime, timedelta
import os
import asyncio
import threading
import time

# Global flag for matplotlib availability
MATPLOTLIB_AVAILABLE = False

# Try to import matplotlib modules
matplotlib_module = None
pyplot_module = None

try:
    matplotlib_module = __import__('matplotlib')
    matplotlib_module.use('Agg')  # Use non-interactive backend
    pyplot_module = __import__('matplotlib.pyplot', fromlist=[''])
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Warning: matplotlib not available. Charts will not be generated.")

class EnhancedStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}  # Cache for performance
        self.cache_lock = threading.Lock()  # Thread lock for cache access
        self.cache_timeout = 300  # 5 minutes
        self.cache_cleanup_interval = 3600  # 1 hour cleanup interval
        if MATPLOTLIB_AVAILABLE:
            self.start_cache_cleanup()
    
    def start_cache_cleanup(self):
        """Start periodic cache cleanup"""
        def cleanup():
            while True:
                time.sleep(self.cache_cleanup_interval)
                with self.cache_lock:
                    current_time = datetime.now()
                    expired_keys = [
                        key for key, (_, timestamp) in self.cache.items()
                        if (current_time - timestamp).total_seconds() > self.cache_timeout
                    ]
                    for key in expired_keys:
                        del self.cache[key]
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def get_cached_data(self, key):
        """Get cached data if available and not expired"""
        with self.cache_lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if (datetime.now() - timestamp).total_seconds() < self.cache_timeout:
                    return data
                else:
                    # Remove expired cache entry
                    del self.cache[key]
        return None
    
    def set_cached_data(self, key, data):
        """Set data in cache"""
        with self.cache_lock:
            self.cache[key] = (data, datetime.now())
    
    def _create_usage_chart_internal(self, dates, counts):
        """Internal method to create usage chart using matplotlib"""
        global MATPLOTLIB_AVAILABLE, pyplot_module
        if not MATPLOTLIB_AVAILABLE or not pyplot_module:
            return None
            
        try:
            fig = pyplot_module.figure(figsize=(10, 6))
            pyplot_module.plot(dates, counts, marker='o', linewidth=2, markersize=8, color='#3498db')
            pyplot_module.title('Bot Usage Over Time (Last 7 Days)', fontsize=16, fontweight='bold')
            pyplot_module.xlabel('Date', fontsize=12)
            pyplot_module.ylabel('Number of Interactions', fontsize=12)
            pyplot_module.xticks(rotation=45)
            pyplot_module.grid(True, alpha=0.3)
            pyplot_module.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            pyplot_module.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            pyplot_module.close(fig)
            return buf
        except Exception as e:
            print(f"Error creating usage chart: {e}")
            return None
    
    def _create_model_usage_chart_internal(self, models, counts):
        """Internal method to create model usage chart using matplotlib"""
        global MATPLOTLIB_AVAILABLE, pyplot_module
        if not MATPLOTLIB_AVAILABLE or not pyplot_module:
            return None
            
        try:
            fig = pyplot_module.figure(figsize=(12, 6))
            bars = pyplot_module.bar(models, counts, color='#9b59b6')
            pyplot_module.title('Model Usage Distribution', fontsize=16, fontweight='bold')
            pyplot_module.xlabel('Models', fontsize=12)
            pyplot_module.ylabel('Number of Uses', fontsize=12)
            pyplot_module.xticks(rotation=45, ha='right')
            pyplot_module.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                pyplot_module.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(count), ha='center', va='bottom')
            
            pyplot_module.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            pyplot_module.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            pyplot_module.close(fig)
            return buf
        except Exception as e:
            print(f"Error creating model usage chart: {e}")
            return None
    
    def _create_code_stats_chart_internal(self, languages, counts):
        """Internal method to create code stats chart using matplotlib"""
        global MATPLOTLIB_AVAILABLE, pyplot_module
        if not MATPLOTLIB_AVAILABLE or not pyplot_module:
            return None
            
        try:
            fig = pyplot_module.figure(figsize=(10, 8))
            colors = pyplot_module.cm.Set3(range(len(languages)))
            wedges, texts, autotexts = pyplot_module.pie(counts, labels=languages, autopct='%1.1f%%', 
                                              startangle=90, colors=colors)
            pyplot_module.title('Code Generation by Language', fontsize=16, fontweight='bold')
            pyplot_module.axis('equal')
            pyplot_module.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            pyplot_module.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            pyplot_module.close(fig)
            return buf
        except Exception as e:
            print(f"Error creating code stats chart: {e}")
            return None
    
    async def generate_usage_chart(self):
        """Generate a usage chart"""
        global MATPLOTLIB_AVAILABLE
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        # Check cache first
        cached_chart = self.get_cached_data("usage_chart")
        if cached_chart:
            # Return a copy of the cached data
            cached_chart.seek(0)
            return io.BytesIO(cached_chart.read())
        
        if not self.bot.db:
            return None
            
        try:
            cursor = self.bot.db.cursor()
            
            # Get daily usage data for the last 7 days
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM conversation_logs 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Extract data properly
            dates = []
            counts = []
            for row in rows:
                dates.append(row[0])  # date
                counts.append(row[1])  # count
            
            # Create the chart using matplotlib
            buf = self._create_usage_chart_internal(dates, counts)
            if buf:
                # Cache the result
                cache_buf = io.BytesIO(buf.read())
                self.set_cached_data("usage_chart", cache_buf)
                
                # Reset buffer for return
                buf.seek(0)
                return buf
            else:
                return None
        except Exception as e:
            print(f"Error generating usage chart: {e}")
            return None
    
    async def generate_model_usage_chart(self):
        """Generate a model usage chart"""
        global MATPLOTLIB_AVAILABLE
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        # Check cache first
        cached_chart = self.get_cached_data("model_usage_chart")
        if cached_chart:
            # Return a copy of the cached data
            cached_chart.seek(0)
            return io.BytesIO(cached_chart.read())
        
        if not self.bot.db:
            return None
            
        try:
            cursor = self.bot.db.cursor()
            
            # Get model usage data
            cursor.execute("""
                SELECT model_used, COUNT(*) as count
                FROM conversation_logs 
                GROUP BY model_used
                ORDER BY count DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Extract data properly
            models = []
            counts = []
            for row in rows:
                models.append(row[0])  # model_used
                counts.append(row[1])  # count
            
            # Create the chart using matplotlib
            buf = self._create_model_usage_chart_internal(models, counts)
            if buf:
                # Cache the result
                cache_buf = io.BytesIO(buf.read())
                self.set_cached_data("model_usage_chart", cache_buf)
                
                # Reset buffer for return
                buf.seek(0)
                return buf
            else:
                return None
        except Exception as e:
            print(f"Error generating model usage chart: {e}")
            return None
    
    async def generate_code_stats_chart(self):
        """Generate a code generation stats chart"""
        global MATPLOTLIB_AVAILABLE
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        # Check cache first
        cached_chart = self.get_cached_data("code_stats_chart")
        if cached_chart:
            # Return a copy of the cached data
            cached_chart.seek(0)
            return io.BytesIO(cached_chart.read())
        
        if not self.bot.db:
            return None
            
        try:
            cursor = self.bot.db.cursor()
            
            # Get code generation stats
            cursor.execute("""
                SELECT language, COUNT(*) as count
                FROM code_generation_logs 
                WHERE success = 1
                GROUP BY language
                ORDER BY count DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Extract data properly
            languages = []
            counts = []
            for row in rows:
                languages.append(row[0])  # language
                counts.append(row[1])  # count
            
            # Create the chart using matplotlib
            buf = self._create_code_stats_chart_internal(languages, counts)
            if buf:
                # Cache the result
                cache_buf = io.BytesIO(buf.read())
                self.set_cached_data("code_stats_chart", cache_buf)
                
                # Reset buffer for return
                buf.seek(0)
                return buf
            else:
                return None
        except Exception as e:
            print(f"Error generating code stats chart: {e}")
            return None
    
    @commands.hybrid_command(
        name="enhanced_stats",
        description="Display enhanced statistics with graphical visualizations"
    )
    async def enhanced_stats(self, ctx: commands.Context):
        """Display enhanced statistics with charts"""
        await ctx.defer()
        
        try:
            global MATPLOTLIB_AVAILABLE
            
            # Create main stats embed
            embed = discord.Embed(
                title="📊 Enhanced Bot Statistics",
                description="Comprehensive analytics with visualizations" if MATPLOTLIB_AVAILABLE else "Comprehensive analytics (charts not available)",
                color=0x9b59b6,
                timestamp=datetime.utcnow()
            )
            
            # Get basic stats with proper error handling
            total_users = 0
            total_conversations = 0
            total_code_generations = 0
            successful_code_generations = 0
            
            if self.bot.db:
                try:
                    cursor = self.bot.db.cursor()
                    
                    # Total users
                    try:
                        cursor.execute("SELECT COUNT(*) FROM user_stats")
                        result = cursor.fetchone()
                        total_users = result[0] if result else 0
                    except Exception as e:
                        print(f"Error fetching user stats: {e}")
                        total_users = 0
                    
                    # Total conversations
                    try:
                        cursor.execute("SELECT COUNT(*) FROM conversation_logs")
                        result = cursor.fetchone()
                        total_conversations = result[0] if result else 0
                    except Exception as e:
                        print(f"Error fetching conversation stats: {e}")
                        total_conversations = 0
                    
                    # Total code generations
                    try:
                        cursor.execute("SELECT COUNT(*) FROM code_generation_logs")
                        result = cursor.fetchone()
                        total_code_generations = result[0] if result else 0
                    except Exception as e:
                        print(f"Error fetching code generation stats: {e}")
                        total_code_generations = 0
                    
                    # Successful code generations
                    try:
                        cursor.execute("SELECT COUNT(*) FROM code_generation_logs WHERE success = 1")
                        result = cursor.fetchone()
                        successful_code_generations = result[0] if result else 0
                    except Exception as e:
                        print(f"Error fetching successful code generation stats: {e}")
                        successful_code_generations = 0
                        
                except Exception as e:
                    print(f"Error accessing database: {e}")
            
            embed.add_field(name="👥 Total Users", value=total_users, inline=True)
            embed.add_field(name="💬 Total Conversations", value=total_conversations, inline=True)
            embed.add_field(name="💻 Total Code Generations", value=total_code_generations, inline=True)
            embed.add_field(name="✅ Successful Code Generations", value=successful_code_generations, inline=True)
            
            # Success rate
            if total_code_generations > 0:
                success_rate = (successful_code_generations / total_code_generations) * 100
                embed.add_field(name="📈 Success Rate", value=f"{success_rate:.1f}%", inline=True)
            
            # Generate and send charts only if matplotlib is available
            if MATPLOTLIB_AVAILABLE:
                files = []
                
                # Usage chart
                usage_chart = await self.generate_usage_chart()
                if usage_chart:
                    usage_file = discord.File(usage_chart, filename="usage_chart.png")
                    files.append(usage_file)
                    embed.set_image(url="attachment://usage_chart.png")
                
                # Send main stats
                await ctx.send(embed=embed, files=files)
                
                # Send additional charts in separate messages
                # Model usage chart
                model_chart = await self.generate_model_usage_chart()
                if model_chart:
                    model_file = discord.File(model_chart, filename="model_chart.png")
                    model_embed = discord.Embed(
                        title="🤖 Model Usage Distribution",
                        color=0x3498db,
                        timestamp=datetime.utcnow()
                    )
                    model_embed.set_image(url="attachment://model_chart.png")
                    await ctx.send(embed=model_embed, file=model_file)
                
                # Code stats chart
                code_chart = await self.generate_code_stats_chart()
                if code_chart:
                    code_file = discord.File(code_chart, filename="code_chart.png")
                    code_embed = discord.Embed(
                        title="💻 Code Generation by Language",
                        color=0x2ecc71,
                        timestamp=datetime.utcnow()
                    )
                    code_embed.set_image(url="attachment://code_chart.png")
                    await ctx.send(embed=code_embed, file=code_file)
            else:
                # Send stats without charts if matplotlib is not available
                embed.set_footer(text="Charts not available - matplotlib not installed")
                await ctx.send(embed=embed)
                
        except Exception as e:
            error_message = f"❌ Error generating enhanced statistics: {str(e)}"
            print(error_message)  # Log the error
            # Try to send a simple error message
            try:
                await ctx.send(error_message)
            except:
                pass

async def setup(bot):
    await bot.add_cog(EnhancedStats(bot))