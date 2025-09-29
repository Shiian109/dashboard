import streamlit as st
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.graph_objects as go

load_dotenv()

# Configuration
DATA_FILE = "new_db.json"
CATEGORIES = ["業務改善・提案", "情報共有・ナレッジ", "雑談・息抜き", "匿名ならではの相談"]
CATEGORY_COLORS = {
    "業務改善・提案": "#0D47A1",
    "情報共有・ナレッジ": "#1976D2", 
    "雑談・息抜き": "#42A5F5",
    "匿名ならではの相談": "#80DEEA"
}

st.set_page_config(page_title="🫧LoungeUp", layout="wide")

# Initialize session state
def init_session_state():
    defaults = {
        'data_loaded': False,
        'logged_in_user': None,
        'users': {},
        'posts': [],
        'answers': {},
        'good_counts': {},
        'bookmark_counts': {},
        'answer_good_counts': {},
        'user_post_state': {},
        'category_filter': 'All',
        'sort_mode': 'latest'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Data persistence
def save_data():
    data = {
        'users': st.session_state.users,
        'posts': st.session_state.posts,
        'answers': st.session_state.answers,
        'good_counts': st.session_state.good_counts,
        'bookmark_counts': st.session_state.bookmark_counts,
        'answer_good_counts': st.session_state.answer_good_counts,
        'logged_in_user': st.session_state.logged_in_user,
        'user_post_state': st.session_state.user_post_state,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for key in ['users', 'posts', 'answers', 'good_counts', 
                    'bookmark_counts', 'answer_good_counts', 
                    'logged_in_user', 'user_post_state']:
            st.session_state[key] = data.get(key, st.session_state.get(key, {}))
        
        # Convert string keys to integers for dictionaries
        for dict_key in ['answers', 'good_counts', 'bookmark_counts', 'answer_good_counts']:
            if isinstance(st.session_state[dict_key], dict):
                st.session_state[dict_key] = {
                    int(k) if k.isdigit() else k: v 
                    for k, v in st.session_state[dict_key].items()
                }

# Helper functions
def categorize_text(text):
    """Simple keyword-based categorization"""
    if not text:
        return '雑談・息抜き'
    t = text.lower()
    if any(k in t for k in ['改善', '提案', '効率', '業務']):
        return '業務改善・提案'
    if any(k in t for k in ['情報', '共有', 'ナレッジ', 'ドキュメント']):
        return '情報共有・ナレッジ'
    if any(k in t for k in ['相談', '悩み', '困っ', '助け']):
        return '匿名ならではの相談'
    return '雑談・息抜き'

def get_user_stats(username):
    """Calculate user statistics"""
    posts_count = len([p for p in st.session_state.posts if p.get('user') == username])
    
    answers_count = sum(
        1 for answers in st.session_state.answers.values()
        for a in answers if a.get('user') == username
    )
    
    bookmarks_received = sum(
        st.session_state.bookmark_counts.get(i, 0)
        for i, p in enumerate(st.session_state.posts)
        if p.get('user') == username
    )
    
    likes_received = sum(
        count.get(j, 0)
        for i, count in st.session_state.answer_good_counts.items()
        for j, a in enumerate(st.session_state.answers.get(i, []))
        if a.get('user') == username
    )
    
    return {
        'posts': posts_count,
        'answers': answers_count,
        'bookmarks': bookmarks_received,
        'likes': likes_received
    }

# Initialize
init_session_state()
if not st.session_state.data_loaded:
    load_data()
    st.session_state.data_loaded = True

# Sidebar - Authentication
with st.sidebar:
    st.markdown("## 🫧 LoungeUp")
    
    if st.session_state.logged_in_user:
        st.success(f"👋 {st.session_state.logged_in_user}さん")
        
        if st.button("ログアウト"):
            st.session_state.logged_in_user = None
            save_data()
            st.rerun()
            
        # User stats
        stats = get_user_stats(st.session_state.logged_in_user)
        st.markdown("### 📊 あなたの統計")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("投稿", f"{stats['posts']}件")
            st.metric("獲得ブックマーク", f"{stats['bookmarks']}件")
        with col2:
            st.metric("回答", f"{stats['answers']}件")
            st.metric("獲得いいね", f"{stats['likes']}件")
    else:
        tab1, tab2 = st.tabs(["ログイン", "新規登録"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("ユーザー名")
                password = st.text_input("パスワード", type="password")
                if st.form_submit_button("ログイン"):
                    user_data = st.session_state.users.get(username)
                    if user_data:
                        pwd = user_data.get('password') if isinstance(user_data, dict) else user_data
                        if pwd == password:
                            st.session_state.logged_in_user = username
                            save_data()
                            st.rerun()
                    st.error("認証に失敗しました")
        
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("ユーザー名")
                new_pass = st.text_input("パスワード", type="password")
                if st.form_submit_button("登録"):
                    if new_user and new_pass and new_user not in st.session_state.users:
                        st.session_state.users[new_user] = {'password': new_pass}
                        st.session_state.logged_in_user = new_user
                        save_data()
                        st.rerun()
                    else:
                        st.error("入力を確認してください")
    
    # Filters
    st.markdown("---")
    st.markdown("### 🔍 フィルタ")
    
    search_query = st.text_input("キーワード検索", key="search_input")
    
    category_filter = st.radio(
        "カテゴリ",
        ["All"] + CATEGORIES,
        index=0
    )
    st.session_state.category_filter = category_filter
    
    sort_mode = st.radio(
        "表示順",
        ["最新順", "ブックマーク順"],
        index=0
    )
    st.session_state.sort_mode = sort_mode

# Main content
main_col, stats_col = st.columns([3, 1])

with stats_col:
    # Community stats
    st.markdown("### 📈 統計")
    
    total_posts = len(st.session_state.posts)
    total_users = len(st.session_state.users)
    total_answers = sum(len(a) for a in st.session_state.answers.values())
    
    st.metric("総投稿数", total_posts)
    st.metric("総ユーザー", total_users)
    st.metric("総回答数", total_answers)
    
    # Popular category
    if st.session_state.posts:
        category_counts = {}
        for post in st.session_state.posts:
            cat = post.get('category', '未分類')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        if category_counts:
            popular_cat = max(category_counts, key=category_counts.get)
            st.metric("人気カテゴリ", popular_cat)

with main_col:
    st.title("🫧 LoungeUp - コミュニティQ&A")
    
    # Post input
    if st.session_state.logged_in_user:
        with st.form("post_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                question = st.text_area("質問を投稿", placeholder="何か聞きたいことはありますか？")
            with col2:
                category = st.selectbox("カテゴリ", CATEGORIES)
            
            if st.form_submit_button("投稿", use_container_width=True):
                if question:
                    new_post = {
                        'user': st.session_state.logged_in_user,
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'question': question,
                        'category': category or categorize_text(question),
                        'postId': len(st.session_state.posts)
                    }
                    st.session_state.posts.append(new_post)
                    save_data()
                    st.rerun()
    else:
        st.info("📝 投稿にはログインが必要です")
    
    st.markdown("---")
    
    # Timeline visualization
    with st.expander("📊 投稿タイムライン", expanded=False):
        if st.session_state.posts:
            df = pd.DataFrame(st.session_state.posts)
            if not df.empty and 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], errors='coerce')
                df = df.dropna(subset=['time'])
                df['date'] = df['time'].dt.date
                
                fig = go.Figure()
                for cat in df['category'].unique():
                    cat_df = df[df['category'] == cat]
                    fig.add_trace(go.Scatter(
                        x=cat_df['date'],
                        y=[cat] * len(cat_df),
                        mode='markers',
                        marker=dict(
                            size=12,
                            color=CATEGORY_COLORS.get(cat, "#999")
                        ),
                        name=cat,
                        hovertemplate='%{x}<br>%{text}',
                        text=cat_df['question']
                    ))
                
                fig.update_layout(
                    height=300,
                    showlegend=True,
                    xaxis_title="日付",
                    yaxis_title="カテゴリ"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Posts display
    st.markdown("### 📋 投稿一覧")
    
    # Filter and sort posts
    filtered_posts = []
    for i, post in enumerate(st.session_state.posts):
        # Category filter
        if st.session_state.category_filter != "All" and post.get('category') != st.session_state.category_filter:
            continue
        
        # Search filter
        if search_query and search_query.lower() not in post.get('question', '').lower():
            continue
        
        filtered_posts.append((i, post))
    
    # Sort
    if st.session_state.sort_mode == "ブックマーク順":
        filtered_posts.sort(key=lambda x: st.session_state.bookmark_counts.get(x[0], 0), reverse=True)
    else:
        filtered_posts.reverse()  # Latest first
    
    # Display posts
    for post_idx, post in filtered_posts[:50]:  # Limit to 50 posts for performance
        with st.container():
            col1, col2, col3 = st.columns([8, 1, 1])
            
            with col1:
                st.markdown(f"**{post['user']}** - {post.get('time', '')}")
                st.write(post['question'])
                
                # Category badge
                st.caption(f"🏷️ {post.get('category', '未分類')}")
            
            with col2:
                # Bookmark button
                bookmark_count = st.session_state.bookmark_counts.get(post_idx, 0)
                if st.button(f"🔖 {bookmark_count}", key=f"bm_{post_idx}"):
                    if st.session_state.logged_in_user:
                        st.session_state.bookmark_counts[post_idx] = bookmark_count + 1
                        save_data()
                        st.rerun()
            
            with col3:
                # Delete button (owner only)
                if st.session_state.logged_in_user == post.get('user'):
                    if st.button("🗑️", key=f"del_{post_idx}"):
                        del st.session_state.posts[post_idx]
                        save_data()
                        st.rerun()
            
            # Answers section
            with st.expander(f"💬 回答 ({len(st.session_state.answers.get(post_idx, []))})", expanded=False):
                answers = st.session_state.answers.get(post_idx, [])
                
                for ans_idx, answer in enumerate(answers):
                    col1, col2 = st.columns([10, 1])
                    with col1:
                        st.markdown(f"**{answer.get('user', '匿名')}** - {answer.get('time', '')}")
                        st.write(answer.get('answer', ''))
                    
                    with col2:
                        likes = st.session_state.answer_good_counts.get(post_idx, {}).get(ans_idx, 0)
                        if st.button(f"👍 {likes}", key=f"like_{post_idx}_{ans_idx}"):
                            if st.session_state.logged_in_user:
                                if post_idx not in st.session_state.answer_good_counts:
                                    st.session_state.answer_good_counts[post_idx] = {}
                                st.session_state.answer_good_counts[post_idx][ans_idx] = likes + 1
                                save_data()
                                st.rerun()
                
                # Answer input
                if st.session_state.logged_in_user:
                    with st.form(f"answer_form_{post_idx}", clear_on_submit=True):
                        answer_text = st.text_input("回答を入力", key=f"ans_input_{post_idx}")
                        if st.form_submit_button("回答する"):
                            if answer_text:
                                if post_idx not in st.session_state.answers:
                                    st.session_state.answers[post_idx] = []
                                st.session_state.answers[post_idx].append({
                                    'answer': answer_text,
                                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    'user': st.session_state.logged_in_user
                                })
                                save_data()
                                st.rerun()
                else:
                    st.info("回答にはログインが必要です")
            
            st.markdown("---")