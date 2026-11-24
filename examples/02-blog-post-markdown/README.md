# Example 02 — Blog post (Markdown, no artifacts)

The skill is not LaTeX-specific. This example gates a Markdown blog post
with a profile tuned for public prose: zero metaphors allowed, Flesch band
raised for readability, vocabulary-overlap comparison off (a blog is not an
ML paper), no artifacts — the claims check is skipped.

## Run it

```bash
python3 scripts/run_all.py \
  --input examples/02-blog-post-markdown/input \
  --config examples/02-blog-post-markdown
# expect: exit 0 — the post passes

# Add this sentence to input/post.md and rerun:
#   "In today's fast-paced digital world, let's dive into how this
#    seamlessly unlocks the true potential of log parsing."
# expect: exit 1 — banned patterns caught, quoted with context
```

Note the YAML trick in `settings.yaml`: single quotes inside single-quoted
strings are doubled (`let''s dive`).
