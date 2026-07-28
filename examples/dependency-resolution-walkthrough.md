# Example: resolving the dependency-modeling estate

A worked walkthrough of the resolution pass (`architecture/dependency-resolution.md`) over the
anonymized example estate (the UDLM repo's `examples/dependency-modeling/`). It shows how
dependencies authored several ways collapse into one effective graph and a derived order — and how
little the resolver actually has to *do*, because most inheritance is plain transitivity.

## The authored estate (15 resources)

- **Power (component chain).** `host-a` contains two power supplies: `psu-a1 → feed-a` and
  `psu-a2 → feed-b` — two independent rails. `host-b` (at the bench) contains one: `psu-b1 →
  feed-wall`. Power is authored on the PSU, not the host.
- **Bundling (a shared node).** `core-services` declares the shared platform dependencies once:
  `depends_on idm` (DirectoryService) + `depends_on dns` (AddressService). `svc-app` and `svc-db`
  each add a single `depends_on core-services`.
- **Scope.** `host-a` and `host-b` carry no identity edge — they share the realm via `tenant_uuid`.
- **App (direct edge).** `svc-app depends_on svc-db`.
- **Location.** `host-a` in `loc-rack`, `host-b` in `loc-bench`.

Each resource authored only its *local* facts — a PSU names its feed, a service names the shared node
it bundles through and the DB it talks to. Nobody hand-wired "host-a depends on feed-a and feed-b" or
"svc-app depends on idm and dns."

## Resolution (build-time, not stored)

1. **Seed** with the authored edges.
2. **Scope derivation** — the one real derivation: `tenant_uuid` is a field, not an edge, so the
   resolver injects `host-a`/`host-b` → the realm's `idm`/`dns` (cycle-safe; the realm's own upstreams
   are excluded).
3. **Everything else is already there.** No bundle-expansion pass, no transitive-chain pass:
   - `svc-app → core-services → {idm, dns}` — svc-app inherits idm+dns as **secondary dependencies**
     by traversal alone. Depend on a node; get its deps. That is all "bundling" is.
   - `host-a → psu-a1 → feed-a` and `host-a → psu-a2 → feed-b` — **host-a's power is the union of both
     feeds**. A coarse "host-a on one UPS" edge would have dropped the second rail.

Effective graph = authored + the scope edges, 0 cycles.

## Derived shutdown order (topological)

| step | resources | note |
|---|---|---|
| 0 | psu-a1, psu-a2, psu-b1, svc-app | leaf consumers stop first |
| 1 | feed-a, feed-b, feed-wall, host-a, svc-db | |
| 2 | core-services, host-b, loc-rack | |
| 3 | **dns, idm**, loc-bench | control-plane gate — identity/DNS hold until last |

Reverse for startup. The payoff: `host-a` stops before **both** its feeds (redundancy honored),
`svc-app` before `core-services` before `idm`/`dns` (bundled secondary deps ordered correctly), and
identity/DNS last — with the resolver only having to derive the scope edges.

## Reproduce

```
python3 shutdown_order.py <path-to>/examples/dependency-modeling   # from the estate-explorer tools
```

See `architecture/dependency-resolution.md` for the mechanics (including the anti-pattern note on why
there is no bundle type) and the UDLM repo's `docs/dependency-modeling.md` for the data-model side.
