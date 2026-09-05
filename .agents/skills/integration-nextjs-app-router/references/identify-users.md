> Source: [PostHog's Identify users documentation](https://posthog.com/docs/product-analytics/identify). The full Markdown index is available at [posthog.com/llms.txt](https://posthog.com/llms.txt).

# Identify users

PostHog assigns browser visitors an anonymous `distinct_id`, stored locally. Events may be captured anonymously until the application knows who the user is.

Call `identify` with the authenticated user's stable, unique ID to associate that anonymous activity with a known person. This links both past and future events made with that browser ID to the user, and creates a person profile when necessary.

```ts
import posthog from 'posthog-js'

posthog.identify(user.id, {
  email: user.email,
  name: user.name,
})
```

Use an immutable ID from the authentication system as the `distinct_id`. Keep email, name, and other attributes as person properties. Never identify multiple people with a shared or non-string value such as `null`, `true`, `"anonymous"`, or `"user"`, because PostHog will merge their data into one person.

## When to identify

Identify the user as soon as their authenticated identity is available:

- On initial application load when the user is already known.
- Immediately after login or sign-up when the user is loaded asynchronously.

Call it once per session unless person properties need to be updated. Repeated calls with identical data during the same page load are ignored.

### Known user during SDK initialization

When the authenticated user is available before the client SDK initializes, identify them in PostHog's `loaded` callback:

```ts
import posthog from 'posthog-js'

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN!, {
  api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
  defaults: '2026-05-30',
  loaded: (client) => {
    if (currentUser?.id) {
      client.identify(currentUser.id, {
        email: currentUser.email,
        name: currentUser.name,
      })
    }
  },
})
```

If user data arrives after initialization, call `posthog.identify()` as soon as it is available instead.

## Reset on logout

Call `reset()` when the user logs out. This prevents later activity in the same browser from being attributed to the previous account, which is especially important on shared devices.

```ts
posthog.reset()
```

Pass `true` only when the device itself should be treated as new for future events:

```ts
posthog.reset(true)
```

## Person properties

The second `identify` argument updates the user's [person properties](https://posthog.com/docs/product-analytics/person-properties). Supply the properties that are currently available whenever identifying a user so the profile stays current.

`$set` and `$set_once` can also update person properties via `capture`, but they are ingestion directives, not event properties. Query them as person properties, not as event filters or breakdowns.

## Client and server identity

Use the same canonical `distinct_id` for browser and backend events so activity belongs to the same person. For Next.js applications that call a separate backend, configure `tracing_headers` for that backend hostname to forward PostHog identity and session context:

```ts
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN!, {
  api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
  defaults: '2026-05-30',
  tracing_headers: ['api.example.com'],
})
```

Use hostnames only. For local development, use `localhost`, not `localhost:3000`; ports are not part of a hostname. `localhost` and `127.0.0.1` are different hostnames.

## Cross-platform deep links

When one platform cannot identify a user yet, preserve the current ID across a deep link:

1. Read the current browser ID with `posthog.get_distinct_id()`.
2. Include it, together with relevant campaign parameters, in the deep-link query string.
3. In the destination app:
   - If it already knows the signed-in user, call `alias()` with the incoming ID.
   - If it does not, call `identify()` with the incoming ID so pre-login activity remains connected. Identify again with the canonical user ID after login.

This associates browser and mobile activity even when authentication is not available on both platforms at the time of navigation.

## Cost consideration

Anonymous events can cost up to four times less to process than identified events. Identify users when there is a product need to associate their activity with a known person; retain anonymous tracking when no stable user ID is available.

## Related documentation

- [PostHog: identifying users](https://posthog.com/docs/product-analytics/identify)
- [PostHog: person properties](https://posthog.com/docs/product-analytics/person-properties)
- [PostHog: person processing](https://posthog.com/docs/how-posthog-works/ingestion-pipeline#2-person-processing)
