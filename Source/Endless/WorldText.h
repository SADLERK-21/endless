#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WorldText.generated.h"

class UWidgetComponent;

// Text placed in the world: signs on the walls, labels, the bedside clock.
// Unlike TextRender (offline fonts, Latin only) it draws with the UI font, so Cyrillic works, and it glows in the dark.
// Reads from the actor's +X side.
UCLASS()
class ENDLESS_API AWorldText : public AActor
{
	GENERATED_BODY()

public:
	AWorldText();

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Text", meta = (MultiLine = true))
	FText Text;

	// Letter height, roughly in cm.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Text", meta = (ClampMin = 1))
	float Size = 16.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Text")
	FLinearColor Color = FLinearColor::White;

protected:
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

private:
	void Refresh();

	UPROPERTY(VisibleAnywhere, Category = "Text")
	TObjectPtr<UWidgetComponent> Widget;
};
