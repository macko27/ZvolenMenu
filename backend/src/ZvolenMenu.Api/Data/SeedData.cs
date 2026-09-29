using Microsoft.EntityFrameworkCore;
using ZvolenMenu.Api.Models;

namespace ZvolenMenu.Api.Data;

public static class SeedData
{
    public static async Task EnsureSeededAsync(AppDbContext db)
    {
        if (await db.Restaurants.AnyAsync())
        {
            return;
        }

        

        var today = DateOnly.FromDateTime(DateTime.Today);

        var uAlexa = R("U Alexa", "Námestie SNP 36/51, Zvolen", 48.57731, 19.12912, "045 533 3811", "https://www.ualexazv.sk/denne-menu");
        var narodnyDom = R("Národný dom", "Námestie SNP 1, Zvolen", 48.57655, 19.12685, "0908 111 001");
        var ambassador = R("Hotel Ambassador", "Námestie SNP 7, Zvolen", 48.57695, 19.12540, "045 532 1100");
        var koliba = R("Koliba pod zámkom", "J. Jiskru 2, Zvolen", 48.57435, 19.12590, "0905 222 333");
        var italia = R("Pizzeria Italia", "J. Kozáčeka 12, Zvolen", 48.57540, 19.12915);
        var uJana = R("Reštaurácia U Jána", "T. G. Masaryka 18, Zvolen", 48.57780, 19.12820, "0907 444 555");
        var asia = R("Asia Garden", "Ul. SNP 28, Zvolen", 48.57380, 19.13040);
        var lesna = R("Reštaurácia Lesná", "Lesnícka 4, Zvolen", 48.58010, 19.12180, "045 533 2211");
        var bistro = R("Bistro Central", "Námestie slobody 3, Zvolen", 48.57590, 19.12410);
        var sport = R("Šport bar Zvolen", "Študentská 9, Zvolen", 48.57195, 19.12355);
        var garden = R("Green Garden", "M. Rázusa 6, Zvolen", 48.57485, 19.12735, "0911 666 777");
        var grill = R("Grill House", "Cesta k nemocnici 5, Zvolen", 48.57890, 19.13320);
        var podzamok = R("Kaviareň Pod vežou", "Námestie SNP 15, Zvolen", 48.57620, 19.12770);

        db.Restaurants.AddRange(
            uAlexa, narodnyDom, ambassador, koliba, italia, uJana, asia,
            lesna, bistro, sport, garden, grill, podzamok);

        

        // Menu types
        var polievka = new MenuType { Name = "Polievka" };
        var predjedlo = new MenuType { Name = "Predjedlo" };
        var hlavne = new MenuType { Name = "Hlavné jedlo" };
        var salat = new MenuType { Name = "Šalát" };
        var dezert = new MenuType { Name = "Dezert" };

        db.MenuTypes.AddRange(polievka, predjedlo, hlavne, salat, dezert);

        // Create daily menus per restaurant
        
        var menus = new List<DailyMenu>
        {
            Menu(narodnyDom, today, null,
                I(1, polievka, "Hovädzí vývar s rezancami", 1.80m, null),
                I(2, polievka, "Cesnaková krémová", 1.80m, null),
                I(3, hlavne, "Vyprážaný rezeň, zemiaková kaša", 6.90m, "bravčové"),
                I(4, hlavne, "Kuracie prsia na smotane, ryža", 6.50m, null),
                I(5, hlavne, "Bryndzové halušky so slaninou", 6.20m, null)),

            Menu(ambassador, today, null,
                I(1, polievka, "Fazuľová s klobásou", 2.00m, null),
                I(2, hlavne, "Sviečková na smotane, knedľa", 7.40m, null),
                I(3, hlavne, "Grilovaný losos, zelenina", 8.90m, null),
                I(4, salat, "Caesar šalát s kuracím mäsom", 5.90m, null)),

            Menu(koliba, today, "Dnes pečieme kačku do 14:00.",
                I(1, polievka, "Kapustnica", 2.20m, null),
                I(2, hlavne, "Pečená kačica, lokše, kapusta", 9.50m, null),
                I(3, hlavne, "Zemiakové placky s bryndzou", 5.80m, null)),

            Menu(uJana, today, null,
                I(1, polievka, "Gulášová", 1.90m, null),
                I(2, hlavne, "Segedínsky guláš, knedľa", 6.40m, null),
                I(3, hlavne, "Vyprážaný syr, hranolky, tatárska", 6.10m, null),
                I(4, dezert, "Palacinky s čokoládou", 2.80m, null)),

            Menu(lesna, today, null,
                I(1, polievka, "Šošovicová", 1.70m, null),
                I(2, hlavne, "Bravčové na hríboch, halušky", 6.80m, null),
                I(3, hlavne, "Pečené kurča, zemiaky", 6.30m, null)),

            Menu(bistro, today, null,
                I(1, polievka, "Paradajková s bazalkou", 1.90m, null),
                I(2, hlavne, "Cestoviny Carbonara", 5.90m, null),
                I(3, hlavne, "Wrap s kuracím mäsom", 5.40m, null),
                I(4, salat, "Quinoa šalát s avokádom", 5.20m, null)),

            Menu(garden, today, "Vegetariánske a vegánske denné menu.",
                I(1, polievka, "Tekvicový krém", 2.10m, null),
                I(2, hlavne, "Cícerové kari, basmati ryža", 6.20m, null),
                I(3, hlavne, "Pečená zelenina, hummus, pita", 5.90m, null),
                I(4, dezert, "Jablkový crumble", 2.50m, null)),

            Menu(podzamok, today, null,
                I(1, polievka, "Kyslá kapustová", 1.60m, null),
                I(2, hlavne, "Kurací steak, šalát", 6.00m, null),
                I(3, hlavne, "Zemiakový šalát s vajíčkom", 4.80m, null))
        };

        db.DailyMenus.AddRange(menus);
        

        await db.SaveChangesAsync();
    }

    private static Restaurant R(string name, string address, double lat, double lng, string? phone = null, string? website = null) =>
        new()
        {
            Name = name,
            Address = address,
            Latitude = lat,
            Longitude = lng,
            Phone = phone,
            Website = website
        };

    private static DailyMenu Menu(Restaurant restaurant, DateOnly date, string? note, params Meal[] items)
    {
        var menu = new DailyMenu
        {
            Restaurant = restaurant,
            MenuDate = date,
            Note = note
        };
        foreach (var item in items)
        {
            item.DailyMenu = menu;
            menu.Items.Add(item);
        }
        return menu;
    }

    private static Meal I(int order, MenuType type, string name, decimal price, string? description = null, string? allergens = null) =>
        new()
        {
            SortOrder = order,
            MenuType = type,
            Name = name,
            Price = price,
            Description = description,
            Allergens = allergens
        };
}
