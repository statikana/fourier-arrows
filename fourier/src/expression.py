from typing import IO
from sympy import symbols, Expr, E as e, exp, pi, I
from dataclasses import dataclass
import json

t = symbols("t")


def i_circle(freq: int) -> exp:
    """Unit circle in the imaginary plane rotating at a frequency `freq`"""
    return e ** (freq * I * 2 * pi * t)


class Term:
    """Represents a term in a Fourier series with a possibly unknown coeffient"""
    def __init__(
        self,
        coef: complex | None,
        n: int
    ):
        self.coef = coef
        self.n = n
        self.circle = i_circle(self.n)

    def at(self, time: float):
        """Gets the value of the term at any given time. Coef must be set"""
        if self.coef is None:
            raise RuntimeError("Coef not determined")

        # c_n * e^2pi * i * t @t=time
        result = (self.coef * self.circle).subs(t, time)
        try:
            return complex(result)  # type: ignore
        except TypeError:
            raise RuntimeError(f"Could not completely resolve term {self.n} at time t={time}")

    def __repr__(self) -> str:
        return f"{self.coef or '__'}e^[{self.n}*2π*t*i]"

class Expression:
    def __init__(self, *, f_t: Expr, n_terms: int) -> None:
        self.f = f_t
        self.n_terms = n_terms

        if (n_terms - 1) % 2 != 0:
            raise ValueError("Must have two terms on either side of constant term (i.e. odd # terms)")
        
        n_max = (n_terms-1)//2
        n_min = -n_max

        self.terms: list[Term] = [
            Term(coef=None, n=n)
            for n in range(n_min, n_max+1)
        ]

    def set_coefs(self) -> None:
        """Isolates each term using integration and sets the .coef attr"""
        cache = open("./src/cache.json", "r+")
        # successfully got coefs from cache file?
        # if self.try_cache(cache) == True:
        #     return
        print(self.f)
        for n, term in enumerate(self.terms):
            # isolate this term by multiplying the function by the opposite circle
            # exponents add (e.g. e^-2 * e^2 = 0), so this term will remain as a constant

            # averaging (integrating) the function from 0-1 isolates all other terms,
            # because all other terms move in circles except for term n (which we just isolated
            # and is now constant)

            # reverse direction circle
            reverse = i_circle(freq=-term.n)
            integrand = self.f * reverse
            average = integrand.integrate((t, 0, 1)).evalf()

            try:
                term.coef = complex(average)
            except TypeError:
                raise RuntimeError(f"Could not completely resolve coef of term {term.n}")

            print(f"\r{n+1}/{len(self.terms)}", end="")

        self.update_cache(cache)
        cache.close()
    
    def try_cache(self, json_file: IO) -> bool:
        """Trys to get this Expression's coefficients from `file. Returns boolean indicating success or failure."""
        # empty cache?
        if not json_file.read(1):
            return False

        json_file.seek(0)
        data = json.load(json_file)

        data.setdefault("cache", {})
        cache = data["cache"]

        key = self.f_key()

        if key not in cache:
            return False

        for n, nums in enumerate(cache[key]):
            self.terms[n].coef = complex(*nums)
        
        print("expr coefs cache hit")
        return True
    
    def update_cache(self, json_file: IO) -> None:
        """Writes this Expression's coefficents to `file`"""
        json_file.seek(0)
        json_file.seek(0)
        if not json_file.read(1):
            data = {"cache": {}}
        else:
            json_file.seek(0)
            data = json.load(json_file)
        key = self.f_key()

        data["cache"][key] = [[term.coef.real, term.coef.imag] for term in self.terms]  # type: ignore
        json_file.seek(0)
        json_file.truncate()
        json.dump(data, json_file)

        print("cache updated")
        
    def f_key(self) -> str:
        return str(self.f) + ",t=" + str(len(self.terms))
        
        
    def at(self, t: float) -> complex:
        if any(term.coef is None for term in self.terms):
            raise RuntimeError("Coef unset")
        return sum(term.at(t) for term in self.terms)
    
    def parts_at(self, t: float) -> list[complex]:
        return [term.at(t) for term in self.terms]