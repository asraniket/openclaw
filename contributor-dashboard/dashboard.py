import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
st.set_page_config(
    page_title="OpenClaw Contributor Dashboard",
    page_icon="🦞",
    layout="wide"
)
# ---- Load data ----
@st.cache_data
def load_data():
    contributors = json.load(open("data/contributors.json"))
    ratings      = json.load(open("data/ratings.json"))
    df  = pd.DataFrame(contributors)
    dfr = pd.DataFrame(ratings)[["login","code_quality","problem_significance",
                                  "review_engagement","consistency","overall","tier","reasoning"]]
    df  = df.merge(dfr, on="login", how="left")
    return df
df = load_data()
# ---- Header ----
st.title("🦞 OpenClaw Contributor Intelligence Dashboard")
st.markdown("Analyzing contributor activity and impact across the OpenClaw open-source project.")
# ---- Top KPIs ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Contributors", len(df))
col2.metric("Total Commits",      int(df["commits"].sum()))
col3.metric("Total PRs Merged",   int(df["prs_merged"].sum()))
col4.metric("Total Reviews",      int(df["reviews_given"].sum()))
st.divider()
# ---- Tabs ----
tab1, tab2, tab3, tab4 = st.tabs(["📊 Volume", "⏱ Recency", "🗂 Scope", "🤖 Autorater"])
# ---- Tab 1: Volume ----
with tab1:
    st.subheader("Top 20 Contributors by Commits")
    top20 = df.sort_values("commits", ascending=False).head(20)
    fig = px.bar(top20, x="login", y="commits",
                 color="commits", color_continuous_scale="Blues",
                 labels={"login": "Contributor", "commits": "Commits"})
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("PRs Opened vs Merged")
    fig2 = px.bar(top20, x="login", y=["prs_opened", "prs_merged"],
                  barmode="group",
                  labels={"login": "Contributor", "value": "Count", "variable": "Metric"})
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)
    st.subheader("Full Contributor Table")
    display_cols = ["login","commits","prs_opened","prs_merged",
                    "issues_opened","reviews_given","comments_made"]
    st.dataframe(df[display_cols].sort_values("commits", ascending=False), use_container_width=True)
# ---- Tab 2: Recency ----
with tab2:
    st.subheader("Recent (last 90 days) vs Historic Activity")
    top20_recent = df.sort_values("commits", ascending=False).head(20)
    fig3 = px.bar(top20_recent, x="login",
                  y=["recent_commits", "historic_commits"],
                  barmode="stack",
                  color_discrete_map={"recent_commits": "#2ecc71", "historic_commits": "#95a5a6"},
                  labels={"login": "Contributor", "value": "Commits", "variable": "Period"})
    fig3.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)
    st.subheader("Contributors with Recent Activity")
    recent_active = df[df["recent_commits"] > 0].sort_values("recent_commits", ascending=False)
    st.metric("Active in last 90 days", len(recent_active))
    st.dataframe(recent_active[["login","recent_commits","historic_commits",
                                 "first_contribution","last_contribution"]],
                 use_container_width=True)
# ---- Tab 3: Scope ----
with tab3:
    st.subheader("Codebase Coverage by Contributor")
    df["dirs_count"] = df["directories"].apply(lambda d: len(d) if isinstance(d, dict) else 0)
    df["files_count"] = df["files_touched"].apply(lambda f: len(f) if isinstance(f, list) else 0)
    top20_scope = df.sort_values("commits", ascending=False).head(20)
    fig4 = px.scatter(top20_scope, x="commits", y="dirs_count",
                      size="prs_merged", hover_data=["login"],
                      labels={"commits": "Total Commits", "dirs_count": "Directories Touched"},
                      title="Commits vs Codebase Breadth")
    st.plotly_chart(fig4, use_container_width=True)
    st.subheader("Select a contributor to see their directory breakdown")
    selected = st.selectbox("Contributor", df["login"].tolist())
    row = df[df["login"] == selected].iloc[0]
    dirs = row["directories"]
    if dirs and isinstance(dirs, dict) and len(dirs) > 0:
        dir_df = pd.DataFrame(list(dirs.items()), columns=["Directory","Commits"])
        dir_df = dir_df.sort_values("Commits", ascending=False)
        fig5 = px.pie(dir_df, names="Directory", values="Commits",
                      title=f"{selected}'s contributions by directory")
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No directory data available for this contributor.")
# ---- Tab 4: Autorater ----
with tab4:
    st.subheader("LLM-Based Contributor Impact Ratings")
    rated = df[df["overall"].notna()].sort_values("overall", ascending=False)
    # Radar chart for top contributor
    st.subheader("Top-rated Contributor — Radar Chart")
    if len(rated) > 0:
        top = rated.iloc[0]
        categories = ["code_quality","problem_significance","review_engagement","consistency"]
        values = [top[c] for c in categories]
        fig6 = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=top["login"]
        ))
        fig6.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])),
                           title=f"Radar: {top['login']}")
        st.plotly_chart(fig6, use_container_width=True)
    # Volume vs Impact scatter
    st.subheader("Commit Volume vs Autorater Score")
    fig7 = px.scatter(rated, x="commits", y="overall",
                      color="tier", hover_data=["login","reasoning"],
                      size="prs_merged",
                      labels={"commits":"Total Commits","overall":"Autorater Score"},
                      title="Volume vs Impact")
    st.plotly_chart(fig7, use_container_width=True)
    # Full ratings table
    st.subheader("Full Ratings Table")
    # Show scores table without reasoning (reasoning is in Deep Dive below)
    rating_cols = ["login", "tier", "overall", "code_quality",
                "problem_significance", "review_engagement", "consistency"]
    st.dataframe(
        rated[rating_cols],
        use_container_width=True,
        height=460,
        column_config={
            "login":                st.column_config.TextColumn("Contributor",    width="medium"),
            "tier":                 st.column_config.TextColumn("Tier",           width="medium"),
            "overall":              st.column_config.NumberColumn("Overall ⭐",   width="small", format="%.1f"),
            "code_quality":         st.column_config.NumberColumn("Code Quality", width="small"),
            "problem_significance": st.column_config.NumberColumn("Problem Sig.", width="small"),
            "review_engagement":    st.column_config.NumberColumn("Reviews",      width="small"),
            "consistency":          st.column_config.NumberColumn("Consistency",  width="small"),
        }
    )
    st.caption("💡 Select a contributor in the Deep Dive section below to see their full reasoning.")
    # Individual deep dive
    st.subheader("Contributor Deep Dive")
    sel2 = st.selectbox("Select contributor", rated["login"].tolist(), key="deepdive")
    row2 = rated[rated["login"] == sel2].iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Code Quality",        row2["code_quality"])
    col2.metric("Problem Significance",row2["problem_significance"])
    col3.metric("Review Engagement",   row2["review_engagement"])
    col4.metric("Consistency",         row2["consistency"])
    st.info(f"**Tier:** {row2['tier']}")
    st.markdown(f"**Reasoning:** {row2['reasoning']}")
