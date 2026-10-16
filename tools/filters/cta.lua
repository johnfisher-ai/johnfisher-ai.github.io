--[[
  Call-to-action box for articles and guide articles.
  Appended to the end of the body, after "Go deeper" and before the endnotes.
  The first two lines are the same everywhere; the optional `cta-source` field in an
  article's front matter adds a last line that names its source, for example:
    cta-source: "Read the full handbook: [Section 1, The evidence](https://...). See the slides: [slide 4](https://...)."
  Listing pages (front matter with `listing`) and pages with `cta: false` get no box.
]]

local PROFILE = "https://www.linkedin.com/in/johnrfisher"

local FIXED = "**Found this useful?** [Follow me on LinkedIn](" .. PROFILE .. ") for the next one.\n\n"
  .. "**Working on this?** [Connect](" .. PROFILE .. ") and tell me what you are seeing.\n"

function Pandoc(doc)
  local meta = doc.meta
  if meta.listing ~= nil or meta.cta == false then
    return doc
  end

  local content = pandoc.read(FIXED, "markdown").blocks
  local source = meta["cta-source"]
  if source ~= nil then
    if pandoc.utils.type(source) == "Inlines" then
      content:insert(pandoc.Para(source))
    elseif pandoc.utils.type(source) == "Blocks" then
      content:extend(source)
    else
      content:insert(pandoc.Para(pandoc.Str(pandoc.utils.stringify(source))))
    end
  end

  doc.blocks:insert(pandoc.Div(content, pandoc.Attr("", {"cta"}, {role = "note", ["aria-label"] = "Follow and connect"})))
  return doc
end
