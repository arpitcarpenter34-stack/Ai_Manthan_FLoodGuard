with open("scripts/verify_major_transformation.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    """        # ---------------------------------------------------------------------
        # 4. AUDIT FEATURE & FLOOD DRIVER ATTRIBUTION (#drivers)
        # ---------------------------------------------------------------------
        print("\\n--- 4. AUDITING FEATURE & FLOOD DRIVER ATTRIBUTION (#drivers) ---")
        await eval_js("navigateTo('drivers')")
        await asyncio.sleep(2.0)""",
    """        # ---------------------------------------------------------------------
        # 4. AUDIT FEATURE & FLOOD DRIVER ATTRIBUTION (#drivers)
        # ---------------------------------------------------------------------
        print("\\n--- 4. AUDITING FEATURE & FLOOD DRIVER ATTRIBUTION (#drivers) ---")
        await eval_js("navigateTo('drivers')")
        await asyncio.sleep(2.5)"""
)

with open("scripts/verify_major_transformation.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated verify script sleep.")

