def step(description, code, var_name=None):
    print("\n" + description)
    if var_name:
        v = var_name + "="
    else:
        v = ""
    input(f">>>{v}{code}")

    try:
        result = eval(code)
        # if hasattr(result, "draw"):
        #     result.draw()
        if var_name:
            globals()[var_name] = result
        return result
    except Exception as e:
        print("Error during execution:", e)
        return None


print(
    """
Welcome to the interactive braid demo!

We'll go step-by-step through braid construction using Artin generators.
Each step waits for you to press Enter. This is a fake console for now, you can not edit the command !
"""
)

step(
    description="""
Step 1: Move the first strand (1) over the second (2).
This is coded as +1 for 'strand 1 over 2' with 3 strands total.
""",
    code="Braid([+1], n_strands=3)",
    var_name="first_upcrossing",
)
step(
    description="""
Step 1: Move the first strand (1) over the second (2).
This is coded as +1 for 'strand 1 over 2' with 3 strands total.
""",
    code="print(first_upcrossing)",
    var_name="",
)

step(
    description="""
You can also draw the resulting braid
""",
    code="Braid([+1], n_strands=3).draw()",
    var_name="first_upcrossing",
)

step(
    description="Step 2: Now move the first strand under the second (coded as -1).",
    code="Braid([-1], n_strands=3).draw()",
    var_name="first_downcrossing",
)

step(
    description="Step 3: Invert the first upcrossing (should give the same as the downcrossing).",
    code="first_upcrossing.inverse().draw()",
    var_name="first_downcrossing_inverted",
)

step(
    description="Step 4: Move the second strand (2) under the third (3).",
    code="Braid([-2], n_strands=3).draw()",
    var_name="second_crossing",
)

step(
    description="Step 5: Combine the upcrossing and second crossing in a list.",
    code="Braid([1, -2], n_strands=3).draw()",
    var_name="b",
)

step(
    description="Step 6: Combine them using the multiplication operator. Be sure to use parenthesis",
    code="(first_upcrossing * second_crossing).draw()",
    var_name="basic_step",
)

step(
    description="Step 7: Repeat this basic step 3 times.",
    code="(basic_step * basic_step * basic_step).draw()",
    var_name="pure_braid",
)

step(
    description="Step 8: Use the exponentiation operator for the same result.",
    code="(basic_step ** 3).draw()",
    var_name="pure_braid",
)
step(
    description="Step 9: Now plot the resulting braid",
    code="pure_braid.plot()",
    var_name="",
)
