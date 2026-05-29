# Row-level security (RLS) setup

Three personas drive RLS — set them up in **Modeling → Manage roles**.

## Role: Executive

- See everything.
- No row filter.

## Role: BU Leader (per business unit)

- See only agents in their business unit.
- Filter on `dim_agent`:

```dax
[business_unit] = USERPRINCIPALNAME()    // if you store the BU as the
                                          // user's UPN — adjust to taste
```

A more typical pattern uses a `dim_user_bu_map` table joined to
`dim_agent[business_unit]`:

```dax
[business_unit] IN
    SELECTCOLUMNS(
        FILTER( dim_user_bu_map, [user] = USERPRINCIPALNAME() ),
        "bu", [business_unit]
    )
```

## Role: Agent Owner

- See only the agents you own.
- Filter on `dim_agent`:

```dax
[owner] = USERPRINCIPALNAME()
```

## Testing roles

In Power BI Desktop: **Modeling → View as → Roles** → tick the role +
"Other user" → enter a UPN. Confirm KPIs and tables filter as expected.

In Power BI Service: **Dataset settings → Security → Add members** to
each role.

## Audit your RLS

Run this quick check before publishing:

| Test | Expected |
| --- | --- |
| Login as `agent-owner@example.com` who owns 2 agents | dashboard shows 2 agents |
| Login as `finance-lead@example.com` (BU Leader) | dashboard shows only Finance BU |
| Login as `cio@example.com` (Executive) | dashboard shows all 60 agents |
