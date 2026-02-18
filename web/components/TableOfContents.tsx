'use client'
import { useEffect, useState } from 'react'

export function TableOfContents() {
  const [headings, setHeadings] = useState<{ id: string; text: string; level: number }[]>([])
  const [activeId, setActiveId] = useState<string>('')

  useEffect(() => {
    // Extract all h2 and h3 headings from the article
    const article = document.querySelector('article')
    if (!article) return

    const elements = article.querySelectorAll('h2, h3')
    const items = Array.from(elements).map((element) => ({
      id: element.id,
      text: element.textContent || '',
      level: parseInt(element.tagName.substring(1)),
    }))

    setHeadings(items)

    // Add IDs to headings if they don't have them
    elements.forEach((element, index) => {
      if (!element.id) {
        const id = element.textContent?.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') || `heading-${index}`
        element.id = id
        items[index].id = id
      }
    })

    // Intersection Observer for active heading
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        })
      },
      { rootMargin: '-100px 0px -80% 0px' }
    )

    elements.forEach((element) => observer.observe(element))

    return () => observer.disconnect()
  }, [])

  if (headings.length === 0) return null

  return (
    <nav className="sticky top-24 hidden xl:block w-64 flex-shrink-0">
      <div className="text-sm">
        <p className="font-semibold text-gray-900 mb-3">On this page</p>
        <ul className="space-y-2 border-l-2 border-gray-200">
          {headings.map((heading) => (
            <li
              key={heading.id}
              className={heading.level === 3 ? 'pl-4' : ''}
            >
              <a
                href={`#${heading.id}`}
                className={`
                  block py-1 px-3 border-l-2 -ml-[2px] transition-colors
                  ${
                    activeId === heading.id
                      ? 'border-blue-600 text-blue-600 font-medium'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-400'
                  }
                `}
              >
                {heading.text}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  )
}
