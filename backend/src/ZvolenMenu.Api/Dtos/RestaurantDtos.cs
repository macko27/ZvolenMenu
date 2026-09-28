namespace ZvolenMenu.Api.Dtos;

public record MealDto(int Id, string Category, string Name, string? Description, decimal Price, string? Allergens);

public record RestaurantDto(
    int Id,
    string Name,
    string Address,
    double Latitude,
    double Longitude,
    string? Phone,
    string? Website,
    bool HasMenu,
    string? Note,
    IReadOnlyList<MealDto> Items);
