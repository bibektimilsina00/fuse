import type { MetadataRoute } from 'next'
import { MARKETING_URL } from '@/shared/constants/routes'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/api/'],
    },
    sitemap: `${MARKETING_URL.replace(/\/$/, '')}/sitemap.xml`,
    host: MARKETING_URL,
  }
}
