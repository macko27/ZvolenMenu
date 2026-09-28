using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ZvolenMenu.Api.Data;
using ZvolenMenu.Api.Dtos;

namespace ZvolenMenu.Api.Controllers;

[ApiController]
[Route("api/restaurants")]
public class RestaurantsController(AppDbContext db) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<RestaurantDto>>> GetAll(
        [FromQuery] DateOnly? date,
        [FromQuery] string? restaurant,
        [FromQuery] string? meal)
    {
        var menuDate = date ?? DateOnly.FromDateTime(DateTime.Today);
        var restaurants = await LoadRestaurantsAsync(menuDate);

        IEnumerable<RestaurantDto> result = restaurants.Select(r => Map(r, menuDate));

        if (!string.IsNullOrWhiteSpace(restaurant))
        {
            var restaurantQuery = restaurant.Trim();
            result = result.Where(r =>
                r.Name.Contains(restaurantQuery, StringComparison.CurrentCultureIgnoreCase)
                || r.Address.Contains(restaurantQuery, StringComparison.CurrentCultureIgnoreCase));
        }

        if (!string.IsNullOrWhiteSpace(meal))
        {
            var mealQuery = meal.Trim();
            result = result.Where(r =>
                r.Items.Any(i =>
                    i.Name.Contains(mealQuery, StringComparison.CurrentCultureIgnoreCase)
                    || (i.Description?.Contains(mealQuery, StringComparison.CurrentCultureIgnoreCase) ?? false)
                    || i.Category.Contains(mealQuery, StringComparison.CurrentCultureIgnoreCase)));
        }

        return Ok(result
            .OrderByDescending(r => r.HasMenu)
            .ThenBy(r => r.Name)
            .ToList());
    }

    [HttpGet("{id:int}")]
    public async Task<ActionResult<RestaurantDto>> GetById(int id, [FromQuery] DateOnly? date)
    {
        var menuDate = date ?? DateOnly.FromDateTime(DateTime.Today);
        var restaurant = await db.Restaurants
            .AsNoTracking()
            .Include(r => r.DailyMenus.Where(m => m.MenuDate == menuDate))
                .ThenInclude(m => m.Items)
                    .ThenInclude(i => i.MenuType)
            .FirstOrDefaultAsync(r => r.Id == id);

        if (restaurant is null)
        {
            return NotFound();
        }

        return Map(restaurant, menuDate);
    }

    private async Task<List<Models.Restaurant>> LoadRestaurantsAsync(DateOnly menuDate) =>
        await db.Restaurants
            .AsNoTracking()
            .Include(r => r.DailyMenus.Where(m => m.MenuDate == menuDate))
                .ThenInclude(m => m.Items)
                    .ThenInclude(i => i.MenuType)
            .OrderBy(r => r.Name)
            .ToListAsync();

    private static RestaurantDto Map(Models.Restaurant restaurant, DateOnly menuDate)
    {
        var menu = restaurant.DailyMenus.FirstOrDefault(m => m.MenuDate == menuDate);
        var items = (menu?.Items ?? [])
            .OrderBy(i => i.SortOrder)
            .Select(i => new MealDto(i.Id, i.MenuType.Name, i.Name, i.Description, i.Price, i.Allergens))
            .ToList();

        return new RestaurantDto(
            restaurant.Id,
            restaurant.Name,
            restaurant.Address,
            restaurant.Latitude,
            restaurant.Longitude,
            restaurant.Phone,
            restaurant.Website,
            menu is not null && items.Count > 0,
            menu?.Note,
            items);
    }
}
